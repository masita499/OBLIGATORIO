#!/bin/bash

TODO=false #(-c)
BASH=false #(-b)
DIR="."

#contadores
Arg1=0
Arg2=0
Arg3=0

#Validacion de argumentos
for i in "$@"; do
    if [ "$i" = "-c" ]; then
        Arg1=$(( Arg1 + 1 ))
        TODO=true
    elif [ "$i" = "-b" ]; then
        Arg2=$(( Arg2 + 1 ))
        BASH=true
    elif [ -d "$i" ]; then
        Arg3=3
        DIR="$i"
    else
        echo "Error: Modificador o argumento inválido: $i" >&2
        echo "Los únicos modificadores permitidos son: -c y -b" >&2
        exit 1
    fi
done

#Errores: repetición de modificadores
if [ "$Arg1" -ge 2 ] || [ "$Arg2" -ge 2 ]; then
    echo "Error: Debe ingresar solo un modificador válido de cada tipo (-c y/o -b)" >&2
    exit 2
fi

#verifica que el parametro sea un directorio valido
if [ ! -d "$DIR" ]; then
    echo "el parametro ingresado "$DIR" no es un directorio" >&2
    exit 2 #termina si el directorio no existe
fi

#Variables
FechaHora=$(date +%d-%m-%y_%H-%M-%S)
BACKUP="backupSetUID_${FechaHora}.tar.gz"
LOG="logcaminos_${FechaHora}.rep"
ListaTEMP="archivos_a_empaquetar.txt" #Lista temporal
ARCHIVOS_A_BACKUP="archivos_finales.txt"
>"$ListaTEMP" #limpia la lista temporal para asegurar que no queden residuos de ejecuciones anteriores 

# if [ "$Arg3" != 3 ]; then
#     archivos=$(find . -type f -user root -perm -4000 -perm -001 2>/dev/null)
# else
archivos=$(find "$DIR" -type f -user root -perm -4000 -perm -001 2>/dev/null)
#fi

for archivo in $archivos; do
    if $BASH; then
        if head -n 1 "$archivo" | grep -q "^#!/bin/bash"; then
        echo "$archivo" >> "$ListaTEMP" #si es un script de bash lo guarda
        fi
    else
        echo "$archivo" >> "$ListaTEMP" #guarda todos los archivos
    fi
done

if [ ! -s "$ListaTEMP" ]; then
    echo "no hay archivos en el directorio "$DIR" que cumplan los requisitos requeridos." >&2
    rm -f $ListaTEMP
    exit 0 #sale si no hay archivos con los requisitos pedidos
fi

if $TODO; then 
    {
        if $BASH; then
            echo "CAMINOS A LOS ARCHIVOS ENCONTRADOS (solo scripts bash):"
        else
            echo "CAMINOS A LOS ARCHIVOS ENCONTRADOS (todos):"
        fi
        cat "$ListaTEMP"
    } > "$LOG"
fi

cp "$ListaTEMP" "$ARCHIVOS_A_BACKUP"

if $TODO && [ -f "$LOG" ]; then
    echo "$LOG" >> "$ARCHIVOS_A_BACKUP"
fi

tar -czf "$BACKUP" -T "$ARCHIVOS_A_BACKUP" 2>/dev/null #Creacion tar.gz

destino="$HOME/Backups"

if [ ! -d $destino ]; then
    mkdir -p "$destino"
    echo "Se creo un directorio "Backups" en el home del usuario para contener los backups"
fi

mv "$BACKUP" "$destino"

#limpieza de archivos usados por el script
rm -f "$ARCHIVOS_A_BACKUP"
rm -f "$ListaTEMP"
#rm -f "$LOG"

#Mensaje final para el usuario
echo "Backup creado: $BACKUP"
if $TODO; then
    echo "Se incluyo el archivo .log: $LOG"
fi

exit 0