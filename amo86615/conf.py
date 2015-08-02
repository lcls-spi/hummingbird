import time, numpy
import analysis.event
import analysis.stack
import analysis.pixel_detector
import analysis.hitfinding
import plotting.image
import plotting.line
import plotting.correlation
import utils.reader
import os,sys
this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(this_dir)
import ipc.mpi

from backend import add_record

# Collect and write out stacks of frames
do_stacks = True
# Common mode correction along fastest changing dimension
do_cmc = True
# Send all events to the frontend
do_showall  = True
show_prop = 0.9

back_gain = "low"
#back_gain = "high"

# ---------------------------------------------------------
# P S A N A
# ---------------------------------------------------------
state = {}
state['Facility'] = 'LCLS'
#state['LCLS/DataSource'] = 'exp=amo86615:run=3'
state['LCLS/DataSource'] = 'shmem=psana.0:stop=no'
state['LCLS/PsanaConf'] = this_dir + '/psana_cfg/pnccd.cfg'

# INJECTOR MOTORS
# ---------------
injector_x_key = "AMO:PPL:MMS:07.RBV"
injector_z_key = "AMO:PPL:MMS:08.RBV"

# ---------------------------------------------------------
# I/O
# ---------------------------------------------------------

front_type = "image"
front_key  = "pnccdFront[%s]" % front_type
back_type = "image"
back_key  = "pnccdBack[%s]" % back_type

# Backgrounds
# -----------
Nbg   = 100
rbg   = 100
obg   = 10
stack_outputs = None
#stack_outputs = ["max","mean"]
bg_front = analysis.stack.Stack(name="bg_front",maxLen=Nbg,outPeriod=obg,reducePeriod=rbg,outputs=stack_outputs)
bg_back = analysis.stack.Stack(name="bg_back",maxLen=Nbg,outPeriod=obg,reducePeriod=rbg,outputs=stack_outputs)
bg_dir = "/reg/neh/home/hantke/amo86615_scratch/stack/"
#bg_dir = this_dir + "/stack"

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

# ---------------------------------------------------------
# PLOTTING PARAMETER
# ---------------------------------------------------------

# Injector position limits
x_min = -20.
x_max = 20
x_bins = 1000
z_min = -20.
z_max = 20.
z_bins = 1000

# Hitrate mean map 
hitrateMeanMapParams = {
    'xmin': x_min,
    'xmax': x_max,
    'ymin': z_min,
    'ymax': z_max,
    'xbins': x_bins,
    'ybins': z_bins,
    'xlabel': 'Injector Position in x (%s)' % injector_x_key,
    'ylabel': 'Injector Position in z (%s)' % injector_z_key
}

# ---------------------------------------------------------
# E V E N T   C A L L
# ---------------------------------------------------------

def onEvent(evt):
    # MPI
    main_slave = ipc.mpi.is_main_slave()
    rank = ipc.mpi.rank

    # ------------------- #
    # INITIAL DIAGNOSTICS #
    # ------------------- #

    # Time measurement
    analysis.event.printProcessingRate()
   
    # Skip frames that do not have the pnCCDs
    try:
        evt[back_type][back_key]
    except TypeError:
        print "No back pnCCD. Skipping event."
        return
    try:
        evt[front_type][front_key]
    except TypeError:
        print "No front pnCCD. Skipping event."
        return

    #analysis.event.printID(evt["eventID"])
    #print evt["photonPixelDetectors"].keys()
    #from IPython.core.debugger import Tracer
    #Tracer()()
    #print evt.keys()
    #evt["psana.PNCCD.FramesV1"]["DetInfo(Camp.0:pnCCD.0)"]

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

    # Simple hitfinding (Count Nr. of lit pixels)
    if back_gain == "high":
        aduThreshold = 2000
        hitscoreMax = 200000
    else:
        aduThreshold = 100
        hitscoreMax = 200000
    
    analysis.hitfinding.countLitPixels(evt, back_type, back_key, aduThreshold=aduThreshold, hitscoreThreshold=3500, hitscoreMax=hitscoreMax, mask=mask_back)
    hit = evt["analysis"]["isHit - " + back_key].data
    hitscore = evt["analysis"]["hitscore - " + back_key].data
    lighton = hitscore > hitscoreMax

    #analysis.hitfinding.countLitPixels(evt, back_type, back_key, aduThreshold=1600, hitscoreThreshold=1500, hitscoreMax=4500, mask=mask_back)

    # Compute the hitrate
    analysis.hitfinding.hitrate(evt, evt["analysis"]["isHit - " + back_key].data, history=10000)
    
    # Plot the hitscore
    plotting.line.plotHistory(evt["analysis"]["hitscore - " + back_key], runningHistogram=True, hmin=0, hmax=100000, bins=100, window=100, history=1000)

    # Plot the hitrate
    plotting.line.plotHistory(evt["analysis"]["hitrate"], label='Hit rate [%]')

    # Plot injector positions
    plotting.line.plotHistory(evt["parameters"][injector_x_key])
    plotting.line.plotHistory(evt["parameters"][injector_z_key])

    # Pulse Energy
    #plotting.line.plotHistory(evt["analysis"]["averagePulseEnergy"])

    # Show hits
    if hit:
        plotting.image.plotImage(evt[front_type_s][front_key_s], 
                                 msg='', name="pnCCD front (hit)")#, vmin=0, vmax=10000, mask=mask_front)     
        plotting.image.plotImage(evt[back_type_s][back_key_s], 
                                 msg='', name="pnCCD back (hit)")#, vmin=0, vmax=10000, mask=mask_back) 

    if do_showall and (show_prop < numpy.random.rand()) and rank > 5:
        plotting.image.plotImage(evt[front_type_s][front_key_s], 
                                 msg='', name="pnCCD front")#, vmin=0, vmax=10000)#, mask=mask_front)     
        plotting.image.plotImage(evt[back_type_s][back_key_s], 
                                 msg='', name="pnCCD back")#, vmin=0, vmax=10000)#, mask=mask_back)     

    # Plot MeanMap of hitrate(y,z)
    if not lighton:
        plotting.correlation.plotMeanMap(evt["parameters"][injector_x_key], evt["parameters"][injector_z_key], hit, plotid='hitrateMeanMap', **hitrateMeanMapParams)
        plotting.correlation.plotMeanMap(evt["parameters"][injector_x_key], evt["parameters"][injector_z_key], hitscore, plotid='hitscoreMeanMap', **hitrateMeanMapParams)

    # COLLECTING BACKGROUND
    if do_stacks and not lighton:
        # Update
        bg_front.add(evt[front_type_s][front_key_s].data)
        bg_back.add(evt[back_type_s][back_key_s].data)

        if rank == 1:
            data = bg_front.mean()
            bg_front_mean = add_record(evt["analysis"], "analysis", "pnCCD front (mean)", data, unit='')
            plotting.image.plotImage(evt["analysis"]["pnCCD front (mean)"], 
                                     msg='', name="pnCCD front (mean)")#, vmin=0, vmax=10000)     
        if rank == 2:
            data = bg_front.max()
            bg_front_max = add_record(evt["analysis"], "analysis", "pnCCD front (max)", data, unit='')
            plotting.image.plotImage(evt["analysis"]["pnCCD front (max)"], 
                                     msg='', name="pnCCD front (max)")#, vmin=0, vmax=10000)     
            
        if rank == 3:
            data = bg_back.mean()
            bg_back_mean = add_record(evt["analysis"], "analysis", "pnCCD back (mean)", data, unit='')
            plotting.image.plotImage(evt["analysis"]["pnCCD back (mean)"], 
                                     msg='', name="pnCCD back (mean)")#, vmin=0, vmax=10000)     
        if rank == 4:
            data = bg_back.max()
            bg_back_max = add_record(evt["analysis"], "analysis", "pnCCD back (max)", data, unit='')
            plotting.image.plotImage(evt["analysis"]["pnCCD back (max)"], 
                                     msg='', name="pnCCD back (max)")#, vmin=0, vmax=10000)     

        if rank == 5:
            # Reduce stack
            bg_front.reduce()
            bg_back.reduce()
            # Write to file
            bg_front.write(evt,directory=bg_dir)
            bg_back.write(evt,directory=bg_dir)

    
