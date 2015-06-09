import os,sys
import numpy
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
this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(this_dir)
import diagnostics


# Flags
# -----

do_testing     = True
do_diagnostics = False
do_sizing      = True

# ---------------------------------------------------------
# P S A N A
# ---------------------------------------------------------

# NOW
experiment = "cxi86715"
# OLD
#experiment = "cxi86415"

state = {
    'Facility':        'LCLS',
    'LCLS/PsanaConf':  ('psana_%s.cfg' % experiment),
}

if do_testing:
    state['LCLS/DataSource'] = ('exp=%s:run=11:xtc' % experiment)
else:
    state['LCLS/DataSource'] = ('exp=%s:run=' % experiment)

# CSPAD 2x2
# ---------

c2x2_ids = {
    'cxi86415': 'Dg3',
    'cxi86715': 'Dg2',
}
c2x2_id = c2x2_ids[experiment]

c2x2_type = "image"
c2x2_key  = "CsPad %s[image]" % c2x2_id

# CSPAD large

clarge_ids = {
    'cxi86415': 'Ds2',
    'cxi86715': 'Ds2',
}
clarge_id = clarge_ids[experiment]

clarge_type = "photons"
clarge_key  = "CsPad %s[photons]" % clarge_id
#clarge_type = "calibrated"
#clarge_key  = "CsPad %s[calibrated]" % clarge_id

# ---------------------------------------------------------
# P A R A M E T E R S
# ---------------------------------------------------------

# Hit finding
# -----------

#aduThreshold      = 20
aduThreshold      = 10
hitscoreThreshold = 1
#hitscoreThreshold = 200

# Sizing
# ------

modelParams = {
    'wavelength':0.12398,
    'pixelsize':110,
    'distance':2160,
    'material':'virus',
}
sizingParams = {
    'd0':100,
    'i0':1,
    'brute_evals':10,
}

# Classification
# --------------

fit_error_threshold  = 1.
diameter_expected    = 70
diameter_error_max   = 30

# Mask
# ----

M_back    = utils.reader.MaskReader(this_dir + "/mask/mask_back.h5","/data/data")
mask_c2x2 = M_back.boolean_mask
(ny_c2x2,nx_c2x2) = mask_c2x2.shape

# Background
# ----------

Nbg = 1000
bg = analysis.stack.Stack(name="bg",maxLen=Nbg)
bg_dir = this_dir + "/stack"

# Plotting
# --------

# Radial averages
radial_tracelen = 100

# Hitrate mean map 
hitrateMeanMapParams = {
    'xmin': -1000,
    'xmax': +1000,
    'ymin': -1000,
    'ymax': +1000,
    'xbins': 10,
    'ybins': 10,
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
    
    # Spit out a lot for debugging
    if do_diagnostics: diagnostics.initial_diagnostics(evt)
    
    # -------- #
    # ANALYSIS #
    # -------- #
    
    # HIT FINDING
    # Simple hit finding by counting lit pixels
    analysis.hitfinding.countLitPixels(evt, c2x2_type, c2x2_key, aduThreshold=aduThreshold, hitscoreThreshold=hitscoreThreshold, mask=mask_c2x2)
    hit = evt["analysis"]["isHit - " + c2x2_key].data

    # COUNT PHOTONS
    # Count photons in different detector regions
    analysis.pixel_detector.totalNrPhotons(evt, c2x2_type, c2x2_key, aduPhoton=1, aduThreshold=0.5)
    analysis.pixel_detector.totalNrPhotons(evt, clarge_type, clarge_key, aduPhoton=1, aduThreshold=0.5)
    analysis.pixel_detector.getCentral4Asics(evt, clarge_type, clarge_key)
        
    if not hit:
        print "MISS (hit score %i > %i)" % (evt["analysis"]["hitscore - " + c2x2_key].data, hitscoreThreshold)
        # COLLECTING BACKGROUND
        # Update background buffer
        bg.add(evt[c2x2_type][c2x2_key].data)
        # Write background to file
        bg.write(evt,directory=bg_dir,interval=Nbg)
    else:
        print "HIT (hit score %i > %i)" % (evt["analysis"]["hitscore - " + c2x2_key].data, hitscoreThreshold)
        if do_sizing:
            # RADIAL SPHERE FIT
            # Find the center of diffraction
            analysis.sizing.findCenter(evt, c2x2_type, c2x2_key, mask=mask_c2x2, maxshift=20, threshold=0.5, blur=4)
            # Calculate radial average
            analysis.pixel_detector.radial(evt, c2x2_type, c2x2_key, mask=mask_c2x2, cx=evt["analysis"]["cx"].data, cy=evt["analysis"]["cy"].data)          
            # Fitting sphere model to get size and intensity
            analysis.sizing.fitSphereRadial(evt, "analysis", "radial distance - " + c2x2_key, "radial average - " + c2x2_key, **dict(modelParams, **sizingParams))
            # Calculate diffraction pattern from fit result 
            analysis.sizing.sphereModel(evt, "analysis", "offCenterX", "offCenterY", "diameter", "intensity", (ny_c2x2,nx_c2x2), poisson=True, **modelParams)
            # Calculate radial average of diffraction pattern from fit result
            analysis.pixel_detector.radial(evt, "analysis", "fit", mask=mask_c2x2, cx=evt["analysis"]["cx"].data, cy=evt["analysis"]["cy"].data)          
            # Decide whether or not the fit was successful
            fit_succeeded = evt["analysis"]["fit error"].data < fit_error_threshold
            good_hit = fit_succeeded
            if fit_succeeded:
                # Decide whether or not this was a good hit, i.e. a hit in the expected size range
                good_hit = abs(evt["analysis"]["diameter"].data - diameter_expected) <= diameter_error_max
               
    # ------------------------ #
    # SEND RESULT TO INTERFACE #
    # ------------------------ #

    # HITFINDING
    # Keep hit history for hitrate plots
    ### DOES NOT WORK LIKE THIS!!!
    plotting.line.plotHistory(evt["analysis"]["isHit - " + c2x2_key])
    # Keep hitscore history
    plotting.line.plotHistory(evt["analysis"]["hitscore - " + c2x2_key])
    #plotting.line.plotHistogram(evt["analysis"]["hitscore - " + c2x2_key], hmin=900, hmax=1100, bins=100, label='', density=False, history=100)

    if not hit:
        
        pass
    
    else:

        hit_msg = ""

        ### NEED CONF FROM JASON ->
        # Injector position
        #plotting.line.plotHistory(evt["analysis"]["injector_x"])
        #plotting.line.plotHistory(evt["analysis"]["injector_y"])
        #plotting.line.plotHistory(evt["analysis"]["injector_z"])
        # Plot MeanMap of hitrate(x,y)
        #x = evt["parameters"]["injector_x"]
        #y = evt["parameters"]["injector_y"]
        #z = hit
        #plotting.correlation.plotMeanMap(x,y,z, plotid='HitrateMeanMap', **hitrateMeanMapParams)
        ### <- NEED CONF FROM JASON
        
        if do_sizing:
            
            # Plot measurement radial average
            plotting.line.plotTrace(evt["analysis"]["radial average - "+c2x2_key], evt["analysis"]["radial distance - "+c2x2_key],tracelen=radial_tracelen)
            # Plot fit radial average
            plotting.line.plotTrace(evt["analysis"]["radial average - fit"], evt["analysis"]["radial distance - fit"], tracelen=radial_tracelen)         
            # Plot fit image
            plotting.image.plotImage(evt["analysis"]["fit"], log=True, mask=mask_c2x2, name="Radial sphere fit result")

            # Fit error history
            plotting.line.plotHistory(evt["analysis"]["fit error"])

            if fit_succeeded:

                # Plot parameter histories
                plotting.line.plotHistory(evt["analysis"]["offCenterX"])
                plotting.line.plotHistory(evt["analysis"]["offCenterY"])
                plotting.line.plotHistory(evt["analysis"]["diameter"], runningHistogram=True)
                plotting.line.plotHistory(evt["analysis"]["intensity"])

                ### NEED CONF ->
                #x = evt["parameters"]["injector_x"]
                #y = evt["parameters"]["injector_y"]
                #z = evt["analysis"]["diameter"]
                #plotting.correlation.plotMeanMap(x,y,z, plotid='DiameterMeanMap', **diameterMeanMapParams)
                #x = evt["parameters"]["injector_x"]
                #y = evt["parameters"]["injector_y"]
                #z = evt["analysis"]["intensity"]
                #plotting.correlation.plotMeanMap(x,y,z, plotid='IntensityMeanMap', **intensityMeanMapParams)
                ### <- NEED CONF
                        
                if good_hit:

                    # Diameter vs. intensity scatter plot
                    plotting.correlation.plotScatter(evt["analysis"]["diameter"], evt["analysis"]["intensity"], plotid='Diameter vs. intensity', history=100)
                    # Plot image of good hit
                    plotting.image.plotImage(evt[c2x2_type][c2x2_key], msg=hit_msg, log=True, mask=mask_c2x2, name="Good hit")

        
        # Plot the glorious shots
        # image
        #plotting.image.plotImage(evt[c2x2_type][c2x2_key], msg=hit_msg, log=True, mask=mask_c2x2)
        plotting.image.plotImage(evt[c2x2_type][c2x2_key], msg=hit_msg, mask=mask_c2x2)
        plotting.line.plotHistogram(evt[c2x2_type][c2x2_key], hmin=-49, hmax=50, bins=100, label='', density=False, history=100)
 
        plotting.image.plotImage(evt[clarge_type][clarge_key])

    # ----------------- #
    # FINAL DIAGNOSTICS #
    # ----------------- #
    
    # Spit out a lot for debugging
    if do_diagnostics: diagnostics.final_diagnostics(evt)

