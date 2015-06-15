import os
import numpy
import analysis.event
import analysis.beamline
import analysis.hitfinding
import analysis.pixel_detector
import analysis.background
import analysis.pixel_detector
import ipc   
import utils.reader
this_dir = os.path.dirname(os.path.realpath(__file__))

state = {
    'Facility': 'LCLS',
    #'LCLS/DataSource': ipc.mpi.get_source(['/data/rawdata/LCLS/cxi/cxic9714/xtc/e419-r0203-s01-c00.xtc', 
    #                                       '/data/rawdata/LCLS/cxi/cxic9714/xtc/e419-r0204-s01-c00.xtc'])
    #'LCLS/DataSource': 'exp=cxi86715:run=10',
    'LCLS/DataSource': 'exp=cxi86415:run=1:xtc',
    #'LCLS/PsanaConf': 'psana_cfg/Ds2.cfg',
    'LCLS/PsanaConf': 'psana_cfg/Dg2.cfg',
}

def onEvent(evt):
    analysis.event.printProcessingRate()
    back = evt["image"]["CsPad Dg3[image]"].data

