#!/bin/bash
#`which mpirun` -H daq-amo-mon02 /reg/neh/operator/amoopr/amo86615/hummingbird/archive/amo86615/run.sh
`which mpirun` -v -tag-output -H daq-amo-mon02,daq-amo-mon03,daq-amo-mon04 --report-pid .pid --map-by ppr:7:node /reg/neh/operator/amoopr/amo86615/hummingbird/amo86615/run.sh 
#`which mpirun` -v -tag-output -H daq-amo-mon02 --report-pid .pid --map-by ppr:2:node /reg/neh/operator/amoopr/amo86615/hummingbird/amo86615/run.sh 
#mpirun -tag-output -v -H daq-cxi-dss07,daq-cxi-dss08,daq-cxi-dss09,daq-cxi-dss10,daq-cxi-dss11 --report-pid .pid --map-by ppr:11:node cxi86715/run.sh
#mpirun -v -H daq-cxi-dss07,daq-cxi-dss08,daq-cxi-dss09,daq-cxi-dss10,daq-cxi-dss11 --report-pid .pid --map-by ppr:8:node ./hummingbird.py -b cxi86715/conf.py