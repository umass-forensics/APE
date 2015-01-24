#!/usr/bin/env bash

tracedir=$1
#should be a full path, sans file extension
outmodel=$2

curdir=`pwd`

exit 0


else
    p=""
fi

cd "$p/synoptic"

find "$tracedir" -name "*apebt*" | xargs $p/synoptic/synoptic.sh -c $p/args/synoptic.txt -o "$outmodel"
