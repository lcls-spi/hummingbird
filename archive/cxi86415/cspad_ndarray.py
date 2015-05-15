from psana import *
import numpy as np
from PSCalib.CalibFileFinder import CalibFileFinder
from psmon import publish
from psmon.plots import XYPlot,Image

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("run", help="run number", type=int)
args = parser.parse_args()
run = args.run

setConfigFile("cspad_ndarray.cfg")

det1 = 'CxiDs1.0:Cspad.0'
det2 = 'CxiDs2.0:Cspad.0'
det2x2 = 'CxiDg3.0:Cspad2x2.0'
ds = DataSource('exp=cxi86415:run=%d'%run)
src1 = Source('DetInfo('+det1+')')
src2 = Source('DetInfo('+det2+')')
src2x2 = Source('DetInfo('+det2x2+')')
cls = ds.env().calibStore()

nevent = 0

for evt in ds.events():
    nevent+=1
    if nevent%10==0: print 'processing event',nevent
    if evt is None:
        print '*** event fetch failed'
        continue
    cam1 = evt.get(ndarray_float64_3,src1,'calibrated')
    cam2 = evt.get(ndarray_float64_3,src2,'calibrated')
    cam2x2 = evt.get(ndarray_float64_3,src2x2,'calibrated')
    if cam1 is None or cam2 is None or cam2x2 is None:
        print cam1.shape
        print cam2.shape
        print cam2x2.shape
    cam1img = evt.get(ndarray_float64_2,src1,'image')
    cam2img = evt.get(ndarray_float64_2,src2,'image')

    if cam1img is None or cam2img is None:
        print cam1img.shape
        print cam2img.shape

    cam = Image(1, "cspad", cam1img) # make a 2D plot
    publish.send("CSPAD", cam) # send to the display

    X = cls.get(ndarray_float64_1, src1, 'x-pix-coords').reshape((32,185,388))
    Y = cls.get(ndarray_float64_1, src1, 'y-pix-coords').reshape((32,185,388))
    #unbondedMask = cls.get(ndarray_int32_1, src1, 'pix_mask')

    cff = CalibFileFinder(ds.env().calibDir(), 'CsPad::CalibV1', pbits=0)
    statusfile = cff.findCalibFile(det1, 'pixel_status', evt.run())
    print statusfile
    pixStatus = np.loadtxt(statusfile)
    print pixStatus.shape
    
    print cam1.shape
    print X.shape
    print Y.shape
    #print unbondedMask.shape

if nevent==0:
    print '*** No cspad events found'
    sys.exit()
