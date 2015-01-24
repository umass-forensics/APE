#!/usr/bin/env bash

# Get the number of unique event in the 
# given dot files

for file in "$@"
do
    echo "$file"
    echo -n "Unique Events"
    grep -oiP '[\-\+][\w_]+' $file | sort | uniq | wc -l
    echo -n "Num States"
    grep -oiP '[\-\+][\w_]+' $file | wc -l
done
