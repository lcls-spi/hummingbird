import time, numpy
import analysis.event
import analysis.stack
import analysis.pixel_detector
import analysis.hitfinding
import analysis.sizing
import analysis.stats
import plotting.image
import plotting.line
import plotting.correlation
import analysis.patterson
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
show_prop = 0.02
# Sizing of hits
do_sizing = True

back_gain = "1/16"
#back_gain = "1/64"
#back_gain = "low"
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
Nbg   = 10
rbg   = 10
obg   = 10000
stack_outputs = None
#stack_outputs = ["max","mean"]
#bg_front = analysis.stack.Stack(name="bg_front",maxLen=Nbg,outPeriod=obg,reducePeriod=rbg,outputs=stack_outputs)
bg_front = analysis.stats.DataStatistics()
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
x_min = -5.
x_max = 5
x_bins = 1000
z_min = 10.
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

event_number = 0

# ---------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------

# Sizing
# ------
binning =4 

centerParams = {
    'x0'       : (520 - (nx_back-1)/2.)/binning,
    'y0'       : (512 - (ny_back-1)/2.)/binning,
    'maxshift' : 10/binning,
    'threshold': 20*binning**2,
    'blur'     : 4,
}
pixelsize_native = 75E-6 
modelParams = {
    'wavelength':0.7963,
    'pixelsize':pixelsize_native/1E-6*binning,
    'distance':735,
    'material':'virus',
}
sizingParams = {
    'd0':100,
    'i0':1,
    'brute_evals':10,
}

res = modelParams["distance"] * 1E-3* modelParams["wavelength"] * 1E-9 / ( pixelsize_native * nx_back )
expected_diameter = 73

# ---------------------------------------------------------
# INTERFACE
# ---------------------------------------------------------

# Image
vmin_back = 0
vmax_back = 1000

# Radial averages
radial_tracelen = 300


# ---------------------------------------------------------
# E V E N T   C A L L
# ---------------------------------------------------------

def onEvent(evt):
    global event_number
    event_number += 1
    # MPI
    main_slave = ipc.mpi.is_main_slave()
    rank = ipc.mpi.rank
    
    #print "zmqserver",ipc.zmq().subscribed

    # ------------------- #
    # INITIAL DIAGNOSTICS #
    # ------------------- #

    # Time measurement
    analysis.event.printProcessingRate()
   
    # Skip frames that do not have the pnCCDs
    try:
        evt[back_type][back_key]
    except (TypeError,KeyError):
        print "No back pnCCD. Skipping event."
        return
    try:
        evt[front_type][front_key]
    except (TypeError,KeyError):
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
        hitscoreThreshold = 4200
        hitscoreMax = 200000
    elif back_gain == "1/16":
        aduThreshold = 30*16
        #hitscoreThreshold = 600
        hitscoreThreshold = 50
        hitscoreMax = 5000000
    elif back_gain == "1/64":
        aduThreshold = 30*4
        hitscoreThreshold = 600
        hitscoreMax = 200000
    else:
        #aduThreshold = 100
        aduThreshold = 30
        hitscoreThreshold = 600
        hitscoreMax = 200000
    #print hitscoreThreshold
    analysis.hitfinding.countLitPixels(evt, back_type, back_key, aduThreshold=aduThreshold, hitscoreThreshold=hitscoreThreshold, hitscoreMax=hitscoreMax, mask=mask_back)
    analysis.hitfinding.countLitPixels(evt, back_type, back_key, aduThreshold=aduThreshold, hitscoreThreshold=9000, hitscoreMax=hitscoreMax, mask=mask_back,label="Golden ")
    hit = evt["analysis"]["isHit - " + back_key].data
    golden_hit = evt["analysis"]["Golden isHit - " + back_key].data

    hitscore = evt["analysis"]["hitscore - " + back_key].data
    lighton = hitscore > hitscoreMax

    #analysis.hitfinding.countLitPixels(evt, back_type, back_key, aduThreshold=1600, hitscoreThreshold=1500, hitscoreMax=4500, mask=mask_back)

    
    # Plot the hitscore
    plotting.line.plotHistory(evt["analysis"]["hitscore - " + back_key], runningHistogram=True, hmin=0, hmax=100000, bins=100, window=100, history=1000)

    # Plot injector positions
    #plotting.line.plotHistory(evt["parameters"][injector_x_key])
    #plotting.line.plotHistory(evt["parameters"][injector_z_key])

    plotting.correlation.plotScatter(evt["parameters"][injector_x_key], evt["analysis"]["hitscore - " + back_key],
                                     plotid='Injector x position vs. hitscore', history=100)

    if hit:
        plotting.line.plotHistory(evt["parameters"][injector_x_key], label='Injector position of hits')

    # Pulse Energy
    #plotting.line.plotHistory(evt["analysis"]["averagePulseEnergy"])


    if do_showall and (event_number % 50 == 0) and rank > 5:
        plotting.image.plotImage(evt[front_type_s][front_key_s], 
                                 msg='', name="pnCCD front")#, vmin=0, vmax=10000)#, mask=mask_front)     
        plotting.image.plotImage(evt[back_type_s][back_key_s], 
                                 msg='', name="pnCCD back")#, vmin=0, vmax=10000)#, mask=mask_back)     

    # Plot MeanMap of hitrate(y,z)
    if not lighton:
        #hit_sim = 1
        plotting.correlation.plotMeanMap(evt["parameters"][injector_x_key], evt["parameters"][injector_z_key], hit,#float(hit_sim),
                                         plotid='hitrateMeanMap', **hitrateMeanMapParams)
        plotting.correlation.plotMeanMap(evt["parameters"][injector_x_key], evt["parameters"][injector_z_key], hitscore,
                                         plotid='hitscoreMeanMap', **hitrateMeanMapParams)

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
#            bg_front.reduce()
            bg_back.reduce()
            # Write to file
#            bg_front.write(evt,directory=bg_dir)
            bg_back.write(evt,directory=bg_dir)

    glorious_hit = False
    if hit and do_sizing:
        # Binning
        analysis.pixel_detector.bin(evt, back_type_s, back_key_s, binning, mask_back)
        #analysis.pixel_detector.bin(evt, front_type_s, front_type_s)
        #front_key_s = "binned image - " + front_key
        mask_back_b = evt["analysis"]["binned mask - " + back_key_s].data
        back_type_b = "analysis"
        back_key_b = "binned image - " + back_key_s
        #front_type_s = "analysis"
        
        #print "HIT (hit score %i > %i)" % (evt["analysis"]["hitscore - " + back_key].data, hitscoreThreshold)
        # CENTER DETERMINATION
        analysis.sizing.findCenter(evt, back_type_b, back_key_b, mask=mask_back_b, **centerParams)
        # RADIAL AVERAGE
        analysis.pixel_detector.radial(evt, back_type_b, back_key_b, mask=mask_back_b, cx=evt["analysis"]["cx"].data, cy=evt["analysis"]["cy"].data)          
        # FIT SPHERE MODEL
        analysis.sizing.fitSphereRadial(evt, "analysis", "radial distance - " + back_key_b, "radial average - " + back_key_b, **dict(modelParams, **sizingParams))
        # DIFFRACTION PATTERN FROM FIT
        analysis.sizing.sphereModel(evt, "analysis", "offCenterX", "offCenterY", "diameter", "intensity", (ny_back/binning,nx_back/binning), poisson=False, **modelParams)
        # RADIAL AVERAGE FIT
        analysis.pixel_detector.radial(evt, "analysis", "fit", mask=mask_back_b, cx=evt["analysis"]["cx"].data, cy=evt["analysis"]["cy"].data)
        # ERRORS
        analysis.sizing.photon_error(evt, back_type_b, back_key_b, "analysis", "fit", 144.)
        analysis.sizing.absolute_error(evt, back_type_b, back_key_b, "analysis", "fit", "absolute error")
        
        # Image of fit
        msg = "diameter: %.2f nm \nIntensity: %.2f mJ/um2\nError: %.2e" %(evt["analysis"]["diameter"].data, evt["analysis"]["intensity"].data, evt["analysis"]["photon error"].data)

        # Multiple particle hit finding
        diameter_pix =  evt["analysis"]["diameter"].data * 1E-9 / res
        analysis.patterson.patterson(evt, back_type_b, back_key_b, mask_back_b, threshold=4. ,diameter_pix=diameter_pix)
        plotting.line.plotHistory(evt["analysis"]["multiple score"], history=1000)
        plotting.line.plotHistory(evt["analysis"]["diameter"], history=1000)
        multiple_hit = evt["analysis"]["multiple score"].data > 100.
        
        glorious_hit = (abs(evt["analysis"]["diameter"].data - expected_diameter) < 10.) and not multiple_hit

        if glorious_hit:
            plotting.image.plotImage(evt[back_type_s][back_key_s], 
                                     msg='', name="pnCCD back (glorious hit)")#, mask=mask_back) 


        if not multiple_hit:
            # HYBRID PATTERN
            hybrid = evt["analysis"]["fit"].data.copy()
            hybrid[:,:520/binning] = evt[back_type_b][back_key_b].data[:,:520/binning]
            add_record(evt["analysis"], "analysis", "Hybrid pattern", hybrid)
            
            error = evt["analysis"]["photon error"].data
            plotting.image.plotImage(evt["analysis"]["Hybrid pattern"], mask=mask_back_b, name="Hybrid pattern", msg=msg)
            plotting.line.plotHistory(evt["analysis"]["photon error"], history=1000)

            plotting.image.plotImage(evt["analysis"]["fit"], log=True, mask=mask_back_b, name="pnCCD: Fit result (radial sphere fit)", msg=msg)
            # Plot measurement radial average
            plotting.line.plotTrace(evt["analysis"]["radial average - "+back_key_b], evt["analysis"]["radial distance - "+back_key_b],tracelen=radial_tracelen)
            # Plot fit radial average
            plotting.line.plotTrace(evt["analysis"]["radial average - fit"], evt["analysis"]["radial distance - fit"], tracelen=radial_tracelen)         
            plotting.line.plotHistory(evt["analysis"]["diameter"], history=1000, name_extension="single hits")
        else:
            plotting.line.plotHistory(evt["analysis"]["diameter"], history=1000, name_extension="multiple hits")

            plotting.image.plotImage(evt[back_type_s][back_key_s], 
                                     msg='', name="pnCCD back (multiple hit)")#, mask=mask_back) 


 
    # Show hits
    if hit:
        plotting.image.plotImage(evt[front_type_s][front_key_s], 
                                 msg='', name="pnCCD front (hit)")#, vmin=0, vmax=10000, mask=mask_front)     
        plotting.image.plotImage(evt[back_type_s][back_key_s], 
                                 msg='', name="pnCCD back (hit)")#, mask=mask_back) 
        if do_sizing:
            plotting.image.plotImage(evt["analysis"]["patterson"], name="Patterson")

        if golden_hit:
            plotting.image.plotImage(evt[front_type_s][front_key_s], 
                                     msg='', name="pnCCD front (Golden hit)")#, vmin=0, vmax=10000, mask=mask_front)     
            plotting.image.plotImage(evt[back_type_s][back_key_s], 
                                     msg='', name="pnCCD back (Golden hit)")#, vmin=0, vmax=10000, mask=mask_back) 


    # Compute the hitrate
    analysis.hitfinding.hitrate(evt, evt["analysis"]["isHit - " + back_key].data, good_hit=glorious_hit, history=10000)

    # Plot the hitrate
    plotting.line.plotHistory(evt["analysis"]["hitrate"], label='Hit rate [%]')
    plotting.line.plotHistory(evt["analysis"]["good hitrate"], label='Hit rate (good hits) [%]')
