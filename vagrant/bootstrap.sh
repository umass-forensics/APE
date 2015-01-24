#!/usr/bin/env bash

apt-get update

apt-get install -y openjdk-7-jre

apt-get install -y curl

#install dot
apt-get install -y graphviz

# Install python easy_install
apt-get install -y python-setuptools
easy_install pip

# Install libssl for uTorrent
apt-get install -y libssl0.9.8:i386

#APE
apt-get install -y build-essential python-dev
apt-get install -y python-twisted
pip install progressbar
pip install zope.interface


#Pytt BT Tracker
pip install tornado

#Synoptic (assuming we want to build it)
apt-get install -y openjdk-7-jdk
apt-get install -y mercurial

#####################################
# Monotorrent
#####################################

apt-get install -y mono-complete



#####################################
# uTorrent
#####################################

#Install BTC to control utorrent
pip install -U https://github.com/bittorrent/btc/tarball/master

curdir=`pwd`
utorrentfile="/vagrant/utorrent-server-3.0-ubuntu-10.10-27079.tar.gz"

cp $utorrentfile /opt/

cd /opt/
tar xvf $utorrentfile
chmod 777 -R utorrent-server-v3_0/
ln -s /opt/utorrent-server-v3_0/utserver /usr/bin/utserver

cd $curdir


#####################################
# Install Transmission
#####################################
apt-get install -y transmission-cli
apt-get install -y transmission-daemon


#####################################
# Vuze
#####################################
apt-get install -y vuze
