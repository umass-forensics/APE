#!/usr/bin/env bash


function clean_up {
    echo "Stopping the print script"
    exit
}

trap clean_up SIGHUP SIGINT SIGTERM

echo -e add "$1\n"

while true; do
    echo -e "show torrents\n"
    sleep 3
done
