#!/bin/sh

mpirun -v -H daq-cxi-dss07,daq-cxi-dss08,daq-cxi-dss09,daq-cxi-dss10,daq-cxi-dss11 --map-by ppr:10:node cxi86715/run.sh