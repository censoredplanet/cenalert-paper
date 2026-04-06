#!/bin/bash

if [[ $# -ne 3 ]] ; then
    echo "usage: $0 <countries> <series_dir> <algorithm>"
    exit 1
fi

COUNTRIES="$1"
export SERIES_DIR="$2"
export ALGORITHM="$3"

hyperparameter_tune() {
    python3 -u -m cenalert.tune_parameters --series ${SERIES_DIR}/$1.csv \
                                           --algorithm ${ALGORITHM} \
                                           --output $1.pkl > $1.log
}

export -f hyperparameter_tune

xargs -P 8 -I {} bash -c 'hyperparameter_tune {}' < "${COUNTRIES}"
