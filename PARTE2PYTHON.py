# Importacion de librerias
import boto3
from dotenv import load_dotenv
import os

# Importacion de credenciales desde .env
load_dotenv()

DB_INSTANCE_CLASS = os.getenv('DB_INSTANCE_CLASS')
ENGINE = os.getenv('ENGINE')
USER_NAME = os.getenv('USER_NAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
bucket = os.getenv('bucket')
datos_config = os.getenv("DATA_AWS_CONFIG").replace("\\n", "\n")
datos_credentials = os.getenv("DATA_AWS_CREDENTIALS").replace("\\n", "\n")

# Constantes
SG_DB_NAME = 'GrupoSeguridadDB'
SG_EC2_NAME = 'GrupoSeguridadDeMiEc2'
DB_INSTANCE_IDENTIFIER = 'Maligno-DB'
TAG_VALUE_NAME = 'Maligno-SRV'
AMI_ID = 'ami-09e6f87a47903347c'
INSTANCE_TYPE = 't2.micro'


def get_or_create_security_group(ec2_client, group_name, description):
    try:
        response = ec2_client.create_security_group(
            GroupName=group_name,
            Description=description
        )
        group_id = response['GroupId']
        print(f"SG creado: {group_name} (ID: {group_id})")
        return group_id
    except ec2_client.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidGroup.Duplicate':
            print(f"El grupo de seguridad '{group_name}' ya existe. Obteniendo ID..")
            response = ec2_client.describe_security_groups(GroupNames=[group_name])
            group_id = response['SecurityGroups'][0]['GroupId']
            print(f"ID del grupo existente: {group_id}")
            return group_id
        else:
            raise


def authorize_ingress_rule(ec2_client, group_id, ip_permissions):
    try:
        ec2_client.authorize_security_group_ingress(
            GroupId=group_id,
            IpPermissions=ip_permissions
        )
        print(f"Regla agregada para el grupo {group_id}")
    except ec2_client.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidPermission.Duplicate':
            print(f"Las reglas ya existen para el grupo {group_id}")
        else:
            raise


def main():
    ec2 = boto3.client('ec2')
    rds = boto3.client('rds')

    # Crear o obtener SG DB
    sg_db_id = get_or_create_security_group(
        ec2,
        SG_DB_NAME,
        'Permitir el acceso al puerto 3306 para MySql desde ec2'
    )

    # Crear o obtener SG EC2
    sg_ec2_id = get_or_create_security_group(
        ec2,
        SG_EC2_NAME,
        'Permitir el acceso desde la instancia EC2 al security group de la DB'
    )

    # Configurar reglas para SG DB (MySQL desde SG EC2)
    authorize_ingress_rule(
        ec2,
        sg_db_id,
        [
            {
                'IpProtocol': 'tcp',
                'FromPort': 3306,
                'ToPort': 3306,
                'UserIdGroupPairs': [{'GroupId': sg_ec2_id}]
            }
        ]
    )

    # Configurar reglas para SG EC2 (https y ssh)
    for port in [443, 22]:
        authorize_ingress_rule(
            ec2,
            sg_ec2_id,
            [
                {
                    'IpProtocol': 'tcp',
                    'FromPort': port,
                    'ToPort': port,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )

    # Crear instancia RDS
    try:
        rds.create_db_instance(
            DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER,
            AllocatedStorage=20,
            DBInstanceClass=DB_INSTANCE_CLASS,
            Engine=ENGINE,
            MasterUsername=USER_NAME,
            MasterUserPassword=DB_PASSWORD,
            VpcSecurityGroupIds=[sg_db_id]
        )
        print(f"Base de datos creada con el nombre {DB_INSTANCE_IDENTIFIER}")
        print("Esperando que la base de datos quede disponible..")
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
    except rds.exceptions.DBInstanceAlreadyExistsFault:
        print(f"La base de datos RDS '{DB_INSTANCE_IDENTIFIER}' ya existe. Obteniendo su endpoint..")
    except Exception as e:
        raise

    db_instance = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
    db_endpoint = db_instance['DBInstances'][0]['Endpoint']['Address']
    print(f"Instancia de Base de Datos disponible en: '{db_endpoint}'")

#script de bash dentro de la Ec2
    user_data_script = f'''#!/bin/bash
# Actualizar el sistema e instalar Mysql
sudo yum update -y
sudo yum install -y mariadb105-server-utils.x86_64

# Instalar AWS CLI v2 si no está instalado
if ! command -v aws &> /dev/null
then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
fi
mkdir /home/ec2-user/.aws

cat <<'EOF' > /home/ec2-user/.aws/config
{datos_config}
EOF

cat <<'EOF' > /home/ec2-user/.aws/credentials
{datos_credentials}
EOF

# Variables de entorno para que la Ec2 sepa donde buscar credenciales
export AWS_PROFILE=default
export AWS_CONFIG_FILE=/home/ec2-user/.aws/config
export AWS_SHARED_CREDENTIALS_FILE=/home/ec2-user/.aws/credentials

# Acceder al S3 desde la Ec2 y descargar obli.sql
aws s3 cp s3://{bucket}/obli.sql /home/ec2-user/obli.sql  >> /home/ec2-user/log_Errores.txt 2>&1

# Volcado del contenido obli.sql en la Mysql de Ec2
mysql -h {db_endpoint} -u {USER_NAME} -p'{DB_PASSWORD}' < /home/ec2-user/obli.sql

'''


    # Buscar si ya existe EC2 con el tag Name
    filters = [
        {"Name": "tag:Name", "Values": [TAG_VALUE_NAME]},
        {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]},
    ]

    paginator = ec2.get_paginator("describe_instances")
    existing_instance_ids = []
    for page in paginator.paginate(Filters=filters):
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                existing_instance_ids.append(instance["InstanceId"])

    if existing_instance_ids:
        print(f"Ya existe la instancia con el Nombre='{TAG_VALUE_NAME}': {', '.join(existing_instance_ids)}")
    else:
        try:
            response = ec2.run_instances(
                ImageId=AMI_ID,
                MinCount=1,
                MaxCount=1,
                InstanceType=INSTANCE_TYPE,
                SecurityGroupIds=[sg_ec2_id],
                UserData=user_data_script,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [{"Key": "Name", "Value": TAG_VALUE_NAME}]
                    }
                ]
            )
            instance_id = response['Instances'][0]['InstanceId']
            print(f"Instancia EC2 creada con el id {instance_id}")
            print("Esperando que la instancia EC2 esté corriendo...")
            waiter = ec2.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])
            print("EC2 creada y corriendo, chuelmito queremos los puntitos..")
        except Exception as e:
            print(f"No se pudo crear la instancia con nombre: '{TAG_VALUE_NAME}'")
            print(e)


if __name__ == '__main__':
    main()