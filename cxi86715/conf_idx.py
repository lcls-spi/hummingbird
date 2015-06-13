import os,sys
import numpy, h5py
import struct
import analysis.event
import analysis.beamline
import analysis.hitfinding
import analysis.pixel_detector
import analysis.stack
import analysis.sizing
import plotting.image
import plotting.line
import plotting.correlation
import ipc  
import utils.reader
import utils.array
this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(this_dir)
import diagnostics


# Flags
# -----

# Sizing
do_sizing         = True
# Front detector activated
do_front          = True
# Do assembly of the front
do_assemble_front = False
# Send the 2x2 images all events to the frontend
do_showall        = False

# Mask
# ----
M_back    = utils.reader.MaskReader(this_dir + "/mask/mask_back.h5","/data/data")
mask_c2x2 = M_back.boolean_mask
(ny_c2x2,nx_c2x2) = mask_c2x2.shape
M_beamstops = utils.reader.MaskReader(this_dir + "/mask/beamstops_back.h5","/data/data")
beamstops_c2x2 = M_beamstops.boolean_mask

# Geometry
# --------
pixel_size = 110E-6
G_front = utils.reader.GeometryReader(this_dir + "/geometry/geometry_front.h5", pixel_size=110.E-6)
x_front = numpy.array(utils.array.cheetahToSlacH5(G_front.x), dtype="int")
y_front = numpy.array(utils.array.cheetahToSlacH5(G_front.y), dtype="int")

# ---------------------------------------------------------
# P S A N A
# ---------------------------------------------------------
state = {}
state['Facility'] = 'LCLS'

run_nr = int(os.environ["HUMMINGBIRD_RUN"])
print run_nr
run = "%04i" % run_nr
# Read times and fiducials from text file
idx_file = '/reg/neh/home/ksa47/convert/data/brights_%s.dat' % run
# Fit results
fitres_file = this_dir + "/fitres/fitres_%s.h5" % run
with open(idx_file, "r") as fp:
    lines = fp.readlines()
    state['times'] = []
    state['fiducials'] = []
    for l in lines:
        state['times'].append(int(l.split("\t")[0]))
        state['fiducials'].append(int(l.split("\t")[1][:-len("\r\n")]))
    # Create fitres file
    with h5py.File(fitres_file, "w") as f:
        N = len(state["times"])
        f["/data/diameter_nm"] = numpy.zeros(N)
        f["/data/diameter_nm"].attrs.modify("axes", ["experiment_identifier:x"])
        f["/data/error"]   = numpy.zeros(N)
        f["/data/error"].attrs.modify("axes", ["experiment_identifier:x"])
        f["/data/intensity_mJ_um2"] = numpy.zeros(N)
        f["/data/intensity_mJ_um2"].attrs.modify("axes", ["experiment_identifier:x"])
        f["/data/img_fit"] = numpy.zeros(shape=(N,ny_c2x2,nx_c2x2), dtype="int32")
        f["/data/img_fit"].attrs.modify("axes", ["experiment_identifier:y:x"])
        f["/data/img_data"] = numpy.zeros(shape=(N,ny_c2x2,nx_c2x2), dtype="int32")
        f["/data/img_data"].attrs.modify("axes", ["experiment_identifier:y:x"])

i_fitres = 0

state['LCLS/DataSource'] = 'exp=cxi86715:run=%s:idx' % run

if do_front:
    state['LCLS/PsanaConf'] = 'psana_cfg/both_cspads.cfg'
else:
    state['LCLS/PsanaConf'] = 'psana_cfg/cspad2x2.cfg'

# CSPAD 2x2
# ---------
c2x2_nat_type = "image"
c2x2_nat_key  = "CsPad Dg2[image]"

# CSPAD large
# -----------
clarge_type = "photons"
#clarge_type = "calibrated"
clarge_key  = "CsPad Ds2[%s]" % clarge_type

# INJECTOR MOTORS
# ---------------
injector_x_key = "CXI:PI2:MMS:01.RBV"
injector_y_key = "CXI:PI2:MMS:02.RBV"
injector_z_key = "CXI:PI2:MMS:03.RBV"

# Background
# ----------
bgall = True
Nbg   = 10
fbg   = 10
bg = analysis.stack.Stack(name="bg",maxLen=Nbg,outPeriod=fbg)
bg_dir = this_dir + "/stack_idx"

# ---------------------------------------------------------
# P A R A M E T E R S
# ---------------------------------------------------------

# Hit finding
# -----------
aduThreshold      = 20
hitscoreThreshold =  0

# Sizing
# ------
centerParams = {
    'x0'       : 256 - (nx_c2x2-1)/2.,
    'y0'       : 217 - (ny_c2x2-1)/2.,
    'maxshift' : 50,
    'threshold': 0.5,
    'blur'     : 4,
}
modelParams = {
    'wavelength':0.1795,
    'pixelsize':110,
    'distance':2400,
    'material':'virus',
}
sizingParams = {
    'd0':100,
    'i0':1,
    'brute_evals':100,
}

# Classification
# --------------
fit_error_threshold  = 1.
diameter_expected    = 70
diameter_error_max   = 30

# Plotting
# --------
# Radial averages
radial_tracelen = 100

x_min = -5
x_max = 0
x_bins = 100
y_min = -40
y_max = -35
y_bins = 100
z_min = -10
z_max = -5
z_bins = 100

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

# Hitscore mean map 
hitscoreMeanMapParams = {
    'xmin': x_min,
    'xmax': x_max,
    'ymin': z_min,
    'ymax': z_max,
    'xbins': x_bins,
    'ybins': z_bins,
    'xlabel': 'Injector Position in x',
    'ylabel': 'Injector Position in z'  
}

# Diameter mean map
diameterMeanMapParams = {
    'xmin': x_min,
    'xmax': x_max,
    'ymin': z_min,
    'ymax': z_max,
    'xbins': 10,
    'ybins': 10,
    'xlabel': 'Injector Position in y',
    'ylabel': 'Injector Position in z'  
}

# Diameter mean map
intensityMeanMapParams = {
    'xmin': x_min,
    'xmax': x_max,
    'ymin': z_min,
    'ymax': z_max,
    'xbins': 10,
    'ybins': 10,
    'xlabel': 'Injector Position in x',
    'ylabel': 'Injector Position in z'  
}

# Image
vmin_c2x2 = 0
vmax_c2x2 = 100
vmin_clarge = 0
vmax_clarge = 10

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

    # Send Fiducials and Timestamp
    plotting.line.plotTimestamp(evt["eventID"]["Timestamp"])
    
    # -------- #
    # ANALYSIS #
    # -------- #

    # AVERAGE PULSE ENERGY
    analysis.beamline.averagePulseEnergy(evt, "pulseEnergies")
    
    # CMC
    analysis.pixel_detector.cmc(evt, c2x2_nat_type, c2x2_nat_key, mask=beamstops_c2x2)
    c2x2_type = "analysis"
    c2x2_key = "cmc - " + c2x2_nat_key

    # HIT FINDING
    # Simple hit finding by counting lit pixels
    analysis.hitfinding.countLitPixels(evt, c2x2_type, c2x2_key, aduThreshold=aduThreshold, hitscoreThreshold=hitscoreThreshold, mask=mask_c2x2)
    hit = evt["analysis"]["isHit - " + c2x2_key].data

    # COUNT PHOTONS
    # Count photons in different detector regions
    analysis.pixel_detector.totalNrPhotons(evt, c2x2_type, c2x2_key, aduPhoton=1, aduThreshold=0.5)
    if do_front:
        analysis.pixel_detector.getCentral4Asics(evt, clarge_type, clarge_key)
        if do_assemble_front:
            analysis.pixel_detector.assemble(evt, clarge_type, clarge_key, x=x_front, y=y_front, nx=400, ny=400, subset=map(lambda i : (i * 8 + 1) * 2, xrange(4)))
        analysis.pixel_detector.totalNrPhotons(evt, clarge_type, clarge_key, aduPhoton=1, aduThreshold=0.5)
        analysis.pixel_detector.totalNrPhotons(evt, "analysis", "central4Asics", aduPhoton=1, aduThreshold=0.5)

    if not hit or bgall:
        # COLLECTING BACKGROUND
        # Update background buffer
        bg.add(evt[c2x2_type][c2x2_key].data)
        # Write background to file
        bg.write(evt,directory=bg_dir)
        
    if hit:

        print "HIT (hit score %i > %i)" % (evt["analysis"]["hitscore - " + c2x2_key].data, hitscoreThreshold)
        good_hit = False
        if do_sizing:
            # RADIAL SPHERE FIT
            # Find the center of diffraction
            analysis.sizing.findCenter(evt, c2x2_type, c2x2_key, mask=mask_c2x2, **centerParams)
            # Calculate radial average
            analysis.pixel_detector.radial(evt, c2x2_type, c2x2_key, mask=mask_c2x2, cx=evt["analysis"]["cx"].data, cy=evt["analysis"]["cy"].data)          
            # Fitting sphere model to get size and intensity
            analysis.sizing.fitSphereRadial(evt, "analysis", "radial distance - " + c2x2_key, "radial average - " + c2x2_key, **dict(modelParams, **sizingParams))
            # Calculate diffraction pattern from fit result 
            analysis.sizing.sphereModel(evt, "analysis", "offCenterX", "offCenterY", "diameter", "intensity", (ny_c2x2,nx_c2x2), poisson=False, **modelParams)
            # Calculate radial average of diffraction pattern from fit result
            analysis.pixel_detector.radial(evt, "analysis", "fit", mask=mask_c2x2, cx=evt["analysis"]["cx"].data, cy=evt["analysis"]["cy"].data)          
            # Decide whether or not the fit was successful
            fit_succeeded = evt["analysis"]["fit error"].data < fit_error_threshold
            if fit_succeeded:
                # Decide whether or not this was a good hit, i.e. a hit in the expected size range
                good_hit = abs(evt["analysis"]["diameter"].data - diameter_expected) <= diameter_error_max

            # Write out info
            global i_fitres
            with h5py.File(fitres_file,"r+") as f:
                f["/data/diameter_nm"][i_fitres] = evt["analysis"]["diameter"].data
                f["/data/intensity_mJ_um2"][i_fitres] = evt["analysis"]["intensity"].data
                f["/data/error"][i_fitres] = evt["analysis"]["fit error"].data
                f["/data/img_fit"][i_fitres] = evt["analysis"]["fit"].data
                f["/data/img_data"][i_fitres] = evt[c2x2_type][c2x2_key].data
            i_fitres += 1
    # ------------------------ #
    # SEND RESULT TO INTERFACE #
    # ------------------------ #

    # Pulse Energy
    # plotting.line.plotHistory(evt["analysis"]["averagePulseEnergy"])
    
    # HITFINDING
    # Keep hit history for hitrate plots
    plotting.line.plotHistory(evt["analysis"]["isHit - " + c2x2_key])
    # Keep hitscore history
    plotting.line.plotHistory(evt["analysis"]["hitscore - " + c2x2_key], runningHistogram=True, hmin=hitscoreThreshold-100, hmax=hitscoreThreshold+100, bins=100, window=100, history=1000)

    # PHOTON COUNTING
    # Keep history of number of photons on the back
    plotting.line.plotHistory(evt["analysis"]["nrPhotons - " + c2x2_key], runningHistogram=True, hmin=hitscoreThreshold-100, hmax=hitscoreThreshold+100, bins=100, window=100, history=1000)


    # Injector position
    x = evt["parameters"][injector_x_key]
    y = evt["parameters"][injector_y_key]
    z = evt["parameters"][injector_z_key]
    plotting.line.plotHistory(x)
    plotting.line.plotHistory(y)
    plotting.line.plotHistory(z)

    # Nr. of photons 
    plotting.line.plotHistory(evt["analysis"]["nrPhotons - " + c2x2_key])
    plotting.line.plotHistory(evt["analysis"]["nrPhotons - " + c2x2_key], runningHistogram=True, hmin=0, hmax=100000, bins=100, window=100, history=1000)
    if do_front:
        plotting.line.plotHistory(evt["analysis"]["nrPhotons - central4Asics"])

    # Plot MeanMap of hitrate(y,z)
    plotting.correlation.plotMeanMap(x, z, evt["analysis"]["hitscore - " + c2x2_key].data, plotid='hitscoreMeanMap', **hitscoreMeanMapParams)

    # Plot ScatterPlot with colored hitscore
    plotting.correlation.plotScatterColor(x,z, evt["analysis"]["hitscore - " + c2x2_key], plotid='hitscoreScatter', vmin=0, vmax=2000, xlabel='Injector X', ylabel='Injectory Z', zlabel='Hitscore')

    if do_showall:
        
        # Image of back detector for all events
        plotting.image.plotImage(evt[c2x2_type][c2x2_key], msg="", mask=mask_c2x2, name="Cspad 2x2: All", vmin=vmin_c2x2, vmax=vmax_c2x2)
        # Histogram of detector for all events
        plotting.line.plotHistogram(evt[c2x2_type][c2x2_key], mask=mask_c2x2, hmin=-100, hmax=100, bins=200, label='Cspad 2x2 pixel value [ADU]')
        
    if hit:

        # ToF
        #plotting.line.plotTrace(evt["ionTOFs"]["Acqiris 0 Channel 1"]) 
        
        # Image of hit
        plotting.image.plotImage(evt[c2x2_type][c2x2_key], msg="", mask=mask_c2x2, name="Cspad 2x2: Hit", vmin=vmin_c2x2, vmax=vmax_c2x2 )      

        # Plot MeanMap of hitrate(y,z)
        plotting.correlation.plotMeanMap(x, z, hit, plotid='HitrateMeanMap', **hitrateMeanMapParams)

        if do_front:
            # Front detector image (central 4 asics) of hit
            #plotting.image.plotImage(evt[clarge_type][clarge_key])
            plotting.image.plotImage(evt["analysis"]["central4Asics"], vmin=vmin_clarge, vmax=vmax_clarge)
            if do_assemble_front:
                plotting.image.plotImage(evt["analysis"]["assembled - " + clarge_key], msg="", name="Cspad large (central 4 asics): Hit", vmin=vmin_clarge, vmax=vmin_clarge)

        if do_sizing:

            # Image of fit
            plotting.image.plotImage(evt["analysis"]["fit"], log=True, mask=mask_c2x2, name="Cspad 2x2: Fit result (radial sphere fit)", vmin=vmin_c2x2, vmax=vmax_c2x2, msg='Size = %.2f [nm]' %evt["analysis"]["diameter"].data)
            
            # Plot measurement radial average
            plotting.line.plotTrace(evt["analysis"]["radial average - "+c2x2_key], evt["analysis"]["radial distance - "+c2x2_key],tracelen=radial_tracelen)
            # Plot fit radial average
            plotting.line.plotTrace(evt["analysis"]["radial average - fit"], evt["analysis"]["radial distance - fit"], tracelen=radial_tracelen)         
            # Plot measurement radial average used
            plotting.line.plotTrace(evt["analysis"]["radial average - used"], evt["analysis"]["radial distance - "+c2x2_key],tracelen=radial_tracelen)
            # Fit error history
            plotting.line.plotHistory(evt["analysis"]["fit error"])

            # Plot parameter histories
            plotting.line.plotHistory(evt["analysis"]["offCenterX"])
            plotting.line.plotHistory(evt["analysis"]["offCenterY"])
            plotting.line.plotHistory(evt["analysis"]["diameter"])
            plotting.line.plotHistory(evt["analysis"]["intensity"])
            #plotting.line.plotHistory(evt["analysis"]["diameter"], runningHistogram=True)
            #plotting.line.plotHistory(evt["analysis"]["intensity"], runningHistogram=True)

            if fit_succeeded:

                plotting.correlation.plotMeanMap(x,y,evt["analysis"]["diameter"].data, plotid='DiameterMeanMap', **diameterMeanMapParams)
                plotting.correlation.plotMeanMap(x,y,evt["analysis"]["intensity"].data, plotid='IntensityMeanMap', **intensityMeanMapParams)
                        
                if good_hit:

                    # Diameter vs. intensity scatter plot
                    plotting.correlation.plotScatter(evt["analysis"]["diameter"], evt["analysis"]["intensity"], plotid='Diameter vs. intensity', history=100)
                    # Image of good hit
                    plotting.image.plotImage(evt[c2x2_type][c2x2_key], msg="", log=True, mask=mask_c2x2, name="Cspad 2x2: Hit and correct particle size", vmin=vmin_c2x2, vmax=vmax_c2x2)
                    
                    if do_front:
                        # Front detector image of good hit
                        plotting.image.plotImage(evt[clarge_type][clarge_key], msg="", name="Cspad large (full): Correct particle size", vmin=vmin_clarge, vmax=vmax_clarge)       
        
