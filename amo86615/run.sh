#!/bin/sh

cd /reg/neh/operator/amoopr/amo86615/hummingbird/

source .bashrc

trap 'kill -USR1 $PID' USR1

./hummingbird.py -b /reg/neh/operator/amoopr/amo86615/hummingbird/amo86615/conf.py &

PID=$!

while true; do
    wait $PID || break
done

