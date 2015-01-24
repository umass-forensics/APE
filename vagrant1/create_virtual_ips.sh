#!/usr/bin/env bash

x=50
end=$((50 + $1))

while [ "$x" -lt "$end" ]
do
    ip="10.0.2.$x"
    echo $ip
    ifconfig eth0:"$x" "$ip"
    x=$(( $x + 1 ))
    
done




