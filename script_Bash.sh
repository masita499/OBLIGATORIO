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

