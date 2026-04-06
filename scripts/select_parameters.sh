#!/bin/bash

if [[ $# -ne 2 ]] ; then
    echo "usage: $0 <parameters_directory> <output_directory>"
    exit 1
fi

for file in $1/*.pkl ; do
    python3 -m cenalert.select_parameters --path ${file} --output $2/$(basename ${file%.pkl})
done
