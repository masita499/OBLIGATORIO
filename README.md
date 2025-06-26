
# Automatización Completa en AWS: Backup, EC2, RDS, S3 y Scripts Bash

Este proyecto consta de **tres componentes automatizados** que trabajan juntos para gestionar un entorno AWS simulado en el contexto educativo de **AWS Academy**. Incluye:

1. Un **script en Bash** que realiza un backup automatizado de archivos especiales del sistema.
2. Un **script en Python (parte 1)** que carga esos archivos a un bucket de Amazon S3.
3. Un **script en Python (parte 2)** que despliega infraestructura en AWS (EC2 + RDS), configura el entorno y restaura una base de datos MySQL.

---

## Flujo general del proyecto

```
[1] Script Bash → backup .tar.gz + log (~/Backups/)
           ↓
[2] Script Python 1 → crea bucket S3 + sube obli.sql + backup
           ↓
[3] Script Python 2 → crea SG, RDS y EC2 + instala herramientas en EC2 + restaura DB
```

---

## Componentes

### 1️ Script Bash – `backup_empaquetador.sh`

Este script empaqueta todos los archivos especiales (con bit SUID y permisos de ejecución para otros) dentro de un directorio específico, cumpliendo los siguientes criterios:

- Archivos con bit SUID y permisos `--x` para "others"
- Opcionalmente, solo scripts con cabecera `#!/bin/bash`
- Genera un backup `.tar.gz` con nombre `backupSetUID_<fecha>.tar.gz`
- Puede generar un archivo `.log` con la lista de archivos incluidos
- Mueve automáticamente el backup a `~/Backups`

#### Parámetros disponibles:

- `-b` → Solo incluye scripts Bash
- `-c` → Genera un archivo `.log` con los caminos encontrados
- `[directorio]` → Ruta a escanear (por defecto: directorio actual)

#### Ejemplo de uso:

```bash
./backup_empaquetador.sh -b -c /usr/bin
```

---

### 2️ script Python Parte 1 – `parte1python.py`

Este script:

- Crea un bucket S3 (si no existe)
- Sube el archivo `obli.sql` ubicado en `~/obli.sql`
- Identifica el backup más reciente en `~/Backups/` con nombre `backupSetUID_*.tar.gz`
- Sube el backup con nombre dinámico tipo `Log_dd-mm-YYYY`

#### Requisitos:

- AWS CLI configurado con credenciales activas
- Archivo `obli.sql` disponible en el home del usuario
- Backup `.tar.gz` generado previamente por el script de Bash

#### Ejecución:

```bash
python3 parte1python.py
```

---

### 3 Script Python Parte 2 – `parte2python.py`

Este script:

- Crea Security Groups para EC2 y RDS
- Despliega una instancia RDS MySQL
- Crea una instancia EC2
- En la EC2: instala `mysql`, `awscli`, configura credenciales y descarga `obli.sql` desde S3
- Ejecuta el volcado SQL sobre la RDS

#### Requiere un archivo `.env`:

```dotenv
DB_INSTANCE_CLASS=db.t3.micro
ENGINE=mysql
USER_NAME=admin
DB_PASSWORD=TuPassword123
bucket=nombre-unico-bucket
DATA_AWS_CONFIG=[contenido con \n]
DATA_AWS_CREDENTIALS=[contenido con \n]
```

#### Ejecución:

```bash
python3 parte2python.py
```

---

## Consideraciones del entorno AWS Academy

- **Credenciales temporales**: Expiran cada 4 hs o al reiniciar el laboratorio.
- **Buckets S3 deben tener nombre único a nivel mundial**.
- **La EC2 necesita credenciales válidas para acceder a S3** → Esto se resuelve dentro del script usando variables del `.env`.
- **La secuencia correcta de ejecución es importante**: primero Bash → luego Python Parte 1 → finalmente Python Parte 2.

---

## Troubleshooting

| Problema | Causa común | Solución |
|---------|-------------|----------|
| `AccessDenied` al subir a S3 | Credenciales vencidas | Reconfigure con `aws configure` |
| `obli.sql` no encontrado | Archivo faltante o ruta incorrecta | Verifique que esté en `~/obli.sql` |
| `No se encontraron backups` | Script Bash no fue ejecutado o sin resultados válidos | Ejecute primero el script Bash |
| Bucket ya existe | Nombre globalmente duplicado | Cambie el nombre del bucket |
| EC2 no accede a S3 | Archivos `.aws/config` y `.aws/credentials` mal generados | Verifique las variables `DATA_AWS_*` en `.env` |

---

## Resultado esperado

- Backup comprimido correctamente en `~/Backups`
- Archivos subidos exitosamente a Amazon S3
- Instancias EC2 y RDS creadas automáticamente
- Base de datos MySQL poblada con el contenido de `obli.sql`
- Todo orquestado y documentado de forma clara, reutilizable y segura
