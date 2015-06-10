#!/bin/sh

source .bashrc
#/hummingbird.py -b examples/psana/mpi/conf.py

trap 'kill -USR1 $PIDÃ' USR1

./hummingbird.py -b cxi86715/conf.py &
PID=$!

while true; do
    wait $PID
done

