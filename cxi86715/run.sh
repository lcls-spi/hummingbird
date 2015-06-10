#!/bin/sh

source .bashrc
#/hummingbird.py -b examples/psana/mpi/conf.py

function trapper
{
    kill -USR1 $PID
    trap trapper USR1
    wait $PID
}
trap trapper USR1

./hummingbird.py -b cxi86715/conf.py &
PID=$!
wait $PID

