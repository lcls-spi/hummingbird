#!/bin/sh

source .bashrc
#/hummingbird.py -b examples/psana/mpi/conf.py

trap 'kill -USR1 $PID' USR1
./hummingbird.py -b cxi86715/conf.py &
PID=$!
wait $PID

