import boto3
from datetime import datetime
import os
import glob

fecha = datetime.now()
nombrelog = fecha.strftime("Log%d-%m-%Y")

s3_client = boto3.client('s3')
bucket_name ="el-maligno-326616"

try:
    s3_client.create_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' creado exitosamente")
except Exception as e:
    print(f"Error al crear el bucket: {e}")

# Subir archivo obli.sql después de crear el bucket

ruta_obli = os.path.expanduser("~/obli.sql")  # Cambiar ruta si está en otro lugar

if os.path.isfile(ruta_obli):
    try:
        s3_client.upload_file(ruta_obli, bucket_name, "obli.sql")
        print(f"Archivo 'obli.sql' subido exitosamente al bucket '{bucket_name}'")
    except Exception as e:
        print(f"Error al subir 'obli.sql': {e}")
else:
    print(f"No se encontró el archivo 'obli.sql' en la ruta {ruta_obli}")

directorio_home = os.path.expanduser("~")
directorio_backup = os.path.join(directorio_home, "Backups")

backups = sorted(
    glob.glob(os.path.join(directorio_backup, "backupSetUID*.tar.gz")),
    key=os.path.getmtime,
    reverse=True
)

if not backups:
    print("No se encontró ningún archivo .tar.gz en ~/Backups")
    exit(1)

archivo_backup = backups[0]
print(f"Archivo a subir: {archivo_backup}")

try:
    s3_client.upload_file(archivo_backup, bucket_name, nombre_log)
    print(f"Archivo subido: '{nombre_log}' en bucket: '{bucket_name}'")
except Exception as e:
    print(f"Error al subir el archivo: {e}")
