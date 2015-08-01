#!/bin/sh

cd /reg/neh/operator/amoopr/amo86615/hummingbird/

source .bashrc
#/hummingbird.py -b examples/psana/mpi/conf.py

trap 'kill -USR1 $PID' USR1

./hummingbird.py -b /reg/neh/operator/amoopr/amo86615/hummingbird/archive/amo86615/conf0.py &
#./hummingbird.py -b cxi86715/conf_alignment.py &
PID=$!

while true; do
    wait $PID || break
done

