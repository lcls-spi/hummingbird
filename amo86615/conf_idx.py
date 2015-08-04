import numpy
import time
import analysis.event
import analysis.stack
import analysis.pixel_detector
import analysis.hitfinding
import analysis.recorder
import plotting.image
import plotting.line
import plotting.correlation
import utils.reader
import os,sys,h5py
import ipc
this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(this_dir)

from backend import add_record

import cxiwriter

# Common mode correction along fastest changing dimension
do_cmc      = True

i_glob = 0

# ---------------------------------------------------------
# P S A N A
# ---------------------------------------------------------

state = {}
state['Facility'] = 'LCLS'
state['LCLS/PsanaConf'] = this_dir + '/psana_cfg/pnccd.cfg'
run_nr = int(os.environ["HUMMINGBIRD_RUN"])
print run_nr
run = "%03i" % run_nr
state['LCLS/DataSource'] = 'exp=amo86615:run=%s:idx' % run

# Read indices from file
state["times"] = []
state["fiducials"] = []
idx_dir = '/reg/d/psdm/amo/amo86615/scratch/ksa47/offline_hits/' + run
filenames = os.listdir(idx_dir)
print filenames
for fn in filenames:
    with h5py.File(idx_dir+"/"+fn,"r") as f:
        m = (numpy.array(f["run"], dtype="int") == int(run_nr))
        if m.sum() > 0:
            state["times"] += list(f["timestamp"][m])
            state["fiducials"] += list(f["fiducial"][m])
state["times"] = state["times"][:10]
state["fiducials"] = state["fiducials"][:10]
N = len(state["times"])

# PNCCD
# -----
front_type = "image"
front_key  = "pnccdFront[%s]" % front_type
back_type = "image"
back_key  = "pnccdBack[%s]" % back_type

# File writer
# -----------
w_dir = '/reg/d/psdm/amo/amo86615/scratch/hantke/patterns'
W = cxiwriter.CXIWriter(w_dir + "/r%s.h5" % run, N)

# ---------------------------------------------------------
# I/O
# ---------------------------------------------------------

# Masks
# -----
M_back    = utils.reader.MaskReader(this_dir + "/mask/mask_back.h5","/data/data")
mask_back = M_back.boolean_mask
(ny_back,nx_back) = mask_back.shape
M_front    = utils.reader.MaskReader(this_dir + "/mask/mask_front.h5","/data/data")
mask_front = M_front.boolean_mask
(ny_front,nx_front) = mask_front.shape

# ---------------------------------------------------------
# E V E N T   C A L L
# ---------------------------------------------------------

def onEvent(evt):

    # ------------------- #
    # INITIAL DIAGNOSTICS #
    # ------------------- #

    # Time measurement
    analysis.event.printProcessingRate()

    # -------------------- #
    # DETECTOR CORRECTIONS #
    # -------------------- #

    if do_cmc:
        # CMC
        analysis.pixel_detector.cmc_pnccd(evt, back_type, back_key)
        analysis.pixel_detector.cmc_pnccd(evt, front_type, front_key)
        back_type_s = "analysis"
        back_key_s = "cmc_pnccd - " + back_key
        front_type_s = "analysis"
        front_key_s = "cmc_pnccd - " + front_key
    if not do_cmc:
        back_type_s = back_type
        back_key_s = back_key
        front_type_s = front_type
        front_key_s = front_key

    # ----- #
    # WRITE #
    # ----- #
        
    global i_glob

    #D_params = {}
    #D_params["hitscore"] = 
    #W.write(D_params, "params", i_glob)

    D_back = {}
    D_back["data"] = evt[back_type_s][back_key_s].data
    D_back["mask"]  = numpy.array(mask_back == False, dtype="uint16")
    D_back["i"] = i_glob
    W.write(D_back, "back_pnccd", i_glob)

    D_front = {}
    D_front["data"] = evt[front_type_s][front_key_s].data
    #D_front["mask"]  = numpy.array(mask_front == False, dtype="uin16")
    D_front["i"] = i_glob
    W.write(D_front, "front_pnccd", i_glob)
       
    i_glob += 1
