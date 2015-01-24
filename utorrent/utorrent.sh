#!/usr/bin/env bash

torrent=$1
inputfile=$2

#Create a new temp directory to store all of the files and such
tmpdir=`mktemp -d`
echo "Using temp directory: $tmpdir"

# Check if they gave us an input file
# Use this to seed the startup state uTorrent.
if [ -n "$2" ]
then
    # The the file name supplied by the user, or extract it from
    # the path.
    if [ -n "$3" ]
    then
        filename=$3
    else
        filename=`basename $2`
    fi

    cp $inputfile $tmpdir/$filename
fi

function clean_up {
    echo "Clean up time"
    btc list | btc remove
    killall utserver
    rm -r $tmpdir
    exit
}

trap clean_up SIGHUP SIGINT SIGTERM


# Running these commands from tmp should cause everything to be downloaded
# here
cd $tmpdir

echo "Killing existing instances of utserver"
killall utserver

#Start the uTorrent server
echo "Starting utserver"
utserver &

echo "waiting for utserver to start."
#Wait for utserver to start up
#btc list will right to stderr if it can't connect to utserver
#if we see something written to stdout, output is not null, assume
#utserver has started
#redirect stderr to keep the output clean
while [ -z $(btc list 2> /dev/null) ]
do
    sleep 1
done

#Remove any existing torrents.
echo "Removing any exisitng torrents."
btc list | btc remove

echo "Adding torret: $torrent"
btc add $torrent

while true; do
    btc list
    sleep 3
done
