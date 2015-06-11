#!/bin/bash
mpirun -v -H daq-cxi-dss07,daq-cxi-dss08,daq-cxi-dss09,daq-cxi-dss10,daq-cxi-dss11 --report-pid .pid --map-by ppr:11:node cxi86715/run.sh
#mpirun -v -H daq-cxi-dss07,daq-cxi-dss08,daq-cxi-dss09,daq-cxi-dss10,daq-cxi-dss11 --report-pid .pid --map-by ppr:8:node ./hummingbird.py -b cxi86715/conf.py