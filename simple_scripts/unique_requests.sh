#!/usr/bin/env bash

#Let's get the unique (index, begin, length) request tuples.

for file in "$@"
do
    echo -n "$file "
    grep -iP ' 2d[45].*' $file | grep -oP 'Info: Request Index \d+, Begin \d+, Length \d+' | wc -l
done 

