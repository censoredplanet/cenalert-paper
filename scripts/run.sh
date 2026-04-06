#!/bin/bash

usage() {
    echo "$0 [-h] <countries> <series_dir> <events_dir> <algorithm> <parameters_dir> <output_dir>"
    exit 1
}

getopts "h:" opt && usage
[[ $# -ne 6 ]] && usage

if [[ ! -d $2 ]] ; then
    echo "Invalid series directory $2"
    exit 1
elif [[ ! -d $3 ]] ; then
    echo "Invalid events directory $3"
    exit 1
elif [[ $4 != "chebyshev" && $4 != "median" && $4 != "iforest" && $4 != "lof" ]] ; then
    echo "Invalid algorithm $4"
    exit 1
elif [[ ! -d $5 ]] ; then
    echo "Invalid parameters directory $5"
    exit 1
fi

cat "$1" | xargs -L 1 -I {} -P 8 \
    python3 -m cenalert.run --path $2/{}.csv \
        --events $3/{}.csv \
        --algorithm $4 \
        --parameters $5/{} \
        --output $6/{}
