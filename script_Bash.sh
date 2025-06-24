
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
