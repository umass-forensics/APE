#!/usr/bin/env bash

torrent=$1
inputfile=$2

#Remove any previous download information
rm -r /home/vagrant/.azureus

#Just remove the contents as we need
#to copy our starting file here
rm -r /home/vagrant/Azureus\ Downloads/*

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

    cp $inputfile /home/vagrant/Azureus\ Downloads/$filename
fi

function clean_up {
    echo "Clean up time"
    rm -r /home/vagrant/.azureus
    rm -r /home/vagrant/Azureus\ Downloads/*
    exit
}

trap clean_up SIGHUP SIGINT SIGTERM

#Azureus shows up as java in ps.
#so we probably don't want to run the kill command.
#killall java


echo "Starting the azureus client."
./print.sh $torrent | azureus -u console


