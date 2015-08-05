import numpy
import time
import analysis.event
import analysis.pixel_detector
import analysis.hitfinding
import analysis.sizing
import analysis.patterson
import plotting.image
import plotting.line
import utils.reader
import os,sys,h5py
import scipy.misc
import ipc
this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(this_dir)

from backend.record import add_record


# Common mode correction along fastest changing dimension
do_cmc      = True
# Do binning
do_binning = True
# Do sizing
do_sizing = True


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
#state["times"] = state["times"][:10]
#state["fiducials"] = state["fiducials"][:10]
state["times"] = numpy.array(state["times"])
state["fiducials"] = numpy.array(state["fiducials"])
tmp = state["times"].argsort()
state["times"] = list(state["times"][tmp])
state["fiducials"] = list(state["fiducials"][tmp])

N = len(state["times"])

# PNCCD
# -----
front_type = "image"
front_key  = "pnccdFront[%s]" % front_type
back_type = "image"
back_key  = "pnccdBack[%s]" % back_type

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

    # ------------------- #
    # INITIAL DIAGNOSTICS #
    # ------------------- #

    # Time measurement
    analysis.event.printProcessingRate()

    # Simple hitfinding (Count Nr. of lit pixels)
    aduThreshold = 30*16
    hitscoreThreshold = 50
    hitscoreMax = 500000000
    analysis.hitfinding.countLitPixels(evt, back_type, back_key, aduThreshold=aduThreshold, hitscoreThreshold=hitscoreThreshold, hitscoreMax=hitscoreMax, mask=mask_back)
    analysis.hitfinding.countLitPixels(evt, back_type, back_key, aduThreshold=aduThreshold, hitscoreThreshold=9000, hitscoreMax=hitscoreMax, mask=mask_back,label="Golden ")
    hit = evt["analysis"]["isHit - " + back_key].data
    golden_hit = evt["analysis"]["Golden isHit - " + back_key].data

    # -------------------- #
    # DETECTOR CORRECTIONS #
    # -------------------- #

    back_type_s = back_type
    back_key_s = back_key
    front_type_s = front_type
    front_key_s = front_key
    mask_back_s = mask_back
    if do_cmc:
        # CMC
        analysis.pixel_detector.cmc_pnccd(evt, back_type_s, back_key_s)
        #analysis.pixel_detector.cmc_pnccd(evt, front_type_s, front_key_s)
        back_type_s = "analysis"
        back_key_s = "cmc_pnccd - " + back_key
        #front_type_s = "analysis"
        #front_key_s = "cmc_pnccd - " + front_key
       

    # ----- #
    # WRITE #
    # ----- #
        
    if hit and do_sizing:
        # Binning
        analysis.pixel_detector.bin(evt, back_type_s, back_key_s, binning, mask_back_s)
        #analysis.pixel_detector.bin(evt, front_type_s, front_type_s)
        #front_key_s = "binned image - " + front_key
        mask_back_b = evt["analysis"]["binned mask - " + back_key_s].data
        back_type_b = "analysis"
        back_key_b = "binned image - " + back_key_s
        #front_type_s = "analysis"
        
        print "HIT (hit score %i > %i)" % (evt["analysis"]["hitscore - " + back_key].data, hitscoreThreshold)
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
 
        diameter_pix =  evt["analysis"]["diameter"].data * 1E-9 / res
        analysis.patterson.patterson(evt, back_type_b, back_key_b, mask_back_b, threshold=4. ,diameter_pix=diameter_pix)
        plotting.image.plotImage(evt["analysis"]["patterson"], name="Patterson")
        plotting.line.plotHistory(evt["analysis"]["multiple score"], history=1000)
