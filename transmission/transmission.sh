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
    killall -r "transmission*"
    rm -r $tmpdir
    exit
}

trap clean_up SIGHUP SIGINT SIGTERM


# Running these commands from tmp should cause everything to be downloaded
# here
cd $tmpdir

echo "Killing existing instances of transmission"
sudo killall -s KILL -r "transmission*"

#Start the server
echo "Starting the Transmission daemon"
transmission-daemon --no-auth --config-dir . --download-dir .

echo "waiting for Transmission-daemon to start."
#Wait for utserver to start up
#transmission-remote will write to stderr if it can't connect to utserver
#if we see something written to stdout, output is not null, assume
#the daemon has started
while [ -z "$(transmission-remote -l 2> /dev/null)" ]
do
    sleep 1
done


echo "Adding torret: $torrent"
transmission-remote -a $torrent

while true; do
    transmission-remote -l
    sleep 3
done
