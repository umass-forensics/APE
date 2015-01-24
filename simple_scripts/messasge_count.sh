#!/usr/bin/env bash

for file in "$@"
do
    echo $file
    # the 2d5 is to make sure we only grab uTorrent log lines
    echo -n ' +piece. '
    grep -niP '2d[45].*\+piece' $file | wc -l
    echo -n ' -piece. '
    grep -niP '2d[45].*\-piece' $file | wc -l
    echo -n ' +request. '
    grep -niP '2d[45].*\+request' $file | wc -l
    echo -n ' +choke. '
    grep -niP '2d[45].*\+choke' $file | wc -l
    echo -n ' +unchoke'
    grep -niP '2d[45].*\+unchoke' $file | wc -l
    echo -n ' +handshake'
    grep -niP '2d[45].*\+handshake' $file | wc -l
done

