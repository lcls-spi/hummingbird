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
import os,sys
import ipc
this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(this_dir)

from backend import add_record

# Collect and write out stacks of frames
do_stacks   = False
# Write stacks to file
do_write_stacks = False and do_stacks
# Common mode correction along fastest changing dimension
do_cmc      = True
# Send all events to the frontend
do_showall  = True
show_prop = 1.

# ---------------------------------------------------------
# P S A N A
# ---------------------------------------------------------
state = {}
state['Facility'] = 'LCLS'
state['LCLS/PsanaConf'] = this_dir + '/psana_cfg/pnccd.cfg'
state['LCLS/DataSource'] = 'exp=amo86615:run=86'

# PNCCD
# -----
front_type = "image"
front_key  = "pnccdFront[%s]" % front_type
back_type = "image"
back_key  = "pnccdBack[%s]" % back_type

# INJECTOR MOTORS
# ---------------
injector_x_key = "AMO:PPL:MMS:07.RBV"
injector_y_key = "AMO:PPL:MMS:08.RBV"
injector_z_key = "AMO:PPL:MMS:09.RBV"

pnccd_z_key = "AMO:LMP:MMS:10.RBV"

# ---------------------------------------------------------
# I/O
# ---------------------------------------------------------

# Backgrounds
# -----------
Nbg   = 100
rbg   = 10
obg   = 10
bg_front = analysis.stack.Stack(name="bg_front",maxLen=Nbg,outPeriod=obg,reducePeriod=rbg)
bg_back = analysis.stack.Stack(name="bg_back",maxLen=Nbg,outPeriod=obg,reducePeriod=rbg)
bg_dir = this_dir + "/stack"

# Masks
# -----
M_back    = utils.reader.MaskReader(this_dir + "/mask/mask_back.h5","/data/data")
mask_back = M_back.boolean_mask
(ny_back,nx_back) = mask_back.shape
#M_beamstops = utils.reader.MaskReader(this_dir + "/mask/beamstops_back.h5","/data/data")
#beamstops_back = M_beamstops.boolean_mask
M_front    = utils.reader.MaskReader(this_dir + "/mask/mask_front.h5","/data/data")
mask_front = M_front.boolean_mask
(ny_front,nx_front) = mask_front.shape

# Recording
# ---------
stuff_to_record = {
    'hitscore_back': ('analysis', 'hitscore - ' + back_key),
    #'hitscore_front': ('analysis', 'hitscore - ' + front_key)
}
recorder_dir = "/reg/d/psdm/amo/amo86615/scratch/hummingbird/offline_hits"
recorder = analysis.recorder.Recorder(recorder_dir, stuff_to_record, ipc.mpi.rank, maxEvents = 100000)

# ---------------------------------------------------------
# PLOTTING PARAMETER
# ---------------------------------------------------------

# Injector position limits
x_min = -3
x_max = -1
x_bins = 50
y_min = -40
y_max = -35
y_bins = 100
z_min = -7
z_max = -5
z_bins = 50

# Hitrate mean map 
hitrateMeanMapParams = {
    'xmin': x_min,
    'xmax': x_max,
    'ymin': z_min,
    'ymax': z_max,
    'xbins': x_bins,
    'ybins': z_bins,
    'xlabel': 'Injector Position in x',
    'ylabel': 'Injector Position in z'  
}

# ---------------------------------------------------------
# E V E N T   C A L L
# ---------------------------------------------------------

def onEvent(evt):

    # ------------------- #
    # INITIAL DIAGNOSTICS #
    # ------------------- #

    # Time measurement
    analysis.event.printProcessingRate()
    #analysis.event.printID(evt["eventID"])
    #print evt["photonPixelDetectors"].keys()
    #from IPython.core.debugger import Tracer
    #Tracer()()
    #for k in evt["parameters"].keys(): print k
    #print evt["parameters"].keys()
    #print evt["parameters"][injector_x_key].data
    print evt["parameters"][pnccd_z_key].data
    #print evt["parameters"][injector_y_key]
    #print evt["parameters"][injector_z_key].data
    #print evt.native_keys()
    #evt["psana.PNCCD.FramesV1"]["DetInfo(Camp.0:pnCCD.0)"]

    # ------- #
    # RECORDS #
    # ------- #
    
    # Injector motor positions
    inj_x = evt["parameters"][injector_x_key]
    inj_y = evt["parameters"][injector_y_key]
    inj_z = evt["parameters"][injector_z_key]
    # Injector pressures
    #p1 = evt["parameters"]["CXI:SDS:REG:01:PRESS"]
    #p2 = evt["parameters"]["CXI:SDS:REG:02:PRESS"]

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
        #front_type_s = front_type
        #front_key_s = front_key
    if not do_cmc:
        back_type_s = back_type
        back_key_s = back_key
        front_type_s = front_type
        front_key_s = front_key

    # COLLECTING BACKGROUND
    if do_stacks:
        # Update
        bg_front.add(evt[front_type_s][front_key_s].data)
        bg_back.add(evt[back_type_s][back_key_s].data)
        # Reduce
        bg_front.reduce()
        bg_back.reduce()
        if do_write_stacks:
            # Write to file
            bg_front.write(evt,directory=bg_dir)
            bg_back.write(evt,directory=bg_dir)
            
    # -------- #
    # ANALYSIS #
    # -------- #

    # Simple hitfinding (Count Nr. of lit pixels)
    analysis.hitfinding.countLitPixels(evt, back_type, back_key, aduThreshold=1600, hitscoreThreshold=2000, hitscoreMax=500000, mask=mask_back)

    # Compute the hitrate
    analysis.hitfinding.hitrate(evt, evt["analysis"]["isHit - " + back_key], history=10000)
    hit = evt["analysis"]["isHit - " + back_key].data
    print hit

    # ------------------------ #
    # Send RESULT TO INTERFACE #
    # ------------------------ #

    # Plot the hitscore
    plotting.line.plotHistory(evt["analysis"]["hitscore - " + back_key], runningHistogram=True, hmin=0, hmax=5000, bins=100, window=100, history=1000)

    # Plot the hitrate
    plotting.line.plotHistory(evt["analysis"]["hitrate"], label='Hit rate [%]')


    # Plot MeanMap of hitrate(y,z)
    if True:
        # TESTING
        x = x_min + numpy.random.rand() * (x_max-x_min)
        add_record(evt["analysis"], "analysis", "x", x, unit='')
        x = evt["analysis"]["x"]
        z = z_min + numpy.random.rand() * (z_max-z_min)
        add_record(evt["analysis"], "analysis", "z", z, unit='')
        z = evt["analysis"]["z"]
        h =  float(numpy.random.randint(2))
        plotting.correlation.plotMeanMap(x, z, h, plotid='hitrateMeanMap', **hitrateMeanMapParams)

    if do_showall and (numpy.random.rand() < show_prop):
        plotting.image.plotImage(evt[front_type_s][front_key_s], 
                                 msg='', name="pnCCD front", vmin=0, vmax=10000, mask=mask_front)     
        plotting.image.plotImage(evt[back_type_s][back_key_s], 
                                 msg='', name="pnCCD back", vmin=0, vmax=10000, mask=mask_back) 

    if do_stacks and (numpy.random.rand() < show_prop):
        data = bg_back.max()
        bg_back_max = add_record(evt["analysis"], "analysis", "pnCCD back (max)", data, unit='')
        plotting.image.plotImage(evt["analysis"]["pnCCD back (max)"], 
                                 msg='', name="pnCCD back (max)", vmin=0, vmax=10000)     

    if hit:
        plotting.image.plotImage(evt[front_type_s][front_key_s], 
                                 msg='', name="pnCCD front (hit)", vmin=0, vmax=10000, mask=mask_front)     
        plotting.image.plotImage(evt[back_type_s][back_key_s], 
                                 msg='', name="pnCCD back (hit)", vmin=0, vmax=10000, mask=mask_back) 

    # ---------#
    # RECORDER #
    # -------- #
    # Record time stamps and other metadata for hits
    if hit:
        recorder.append(evt)

    time.sleep(1)
    
