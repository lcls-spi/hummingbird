import os
import numpy
import analysis.event
import analysis.beamline
import analysis.hitfinding
import analysis.pixel_detector
import analysis.stack
import analysis.pixel_detector
import plotting.image
import ipc   
import utils.reader
import diagnostics
this_dir = os.path.dirname(os.path.realpath(__file__))

# Flags
# -----

do_testing     = True
do_diagnostics = True
do_sizing      = True

# ----------------------------------------------------------------------------------------------------------------------------------------------------------
# P S A N A
# ----------------------------------------------------------------------------------------------------------------------------------------------------------

state = {
    'Facility':        'LCLS',
    'LCLS/PsanaConf':  'psana_cfg/Dg2.cfg',
}

if do_testing:
    state['LCLS/DataSource'] = 'exp=cxi86415:run=1:xtc',
else:
    state['LCLS/DataSource'] = 'exp=cxi86715:run=',

# CSPAD 2x2
# ---------

c2x2_type = "image"
c2x2_key  = "CsPad Dg3[image]"

# ----------------------------------------------------------------------------------------------------------------------------------------------------------
# P A R A M E T E R S
# ----------------------------------------------------------------------------------------------------------------------------------------------------------

# Hit finding
# -----------

aduThreshold      = 10
hitscoreThreshold = 200

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

Nbg = 500
bg = analysis.stack.Stack(name="bg",maxLen=Nbg)

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


# ----------------------------------------------------------------------------------------------------------------------------------------------------------
# E V E N T   C A L L
# ----------------------------------------------------------------------------------------------------------------------------------------------------------

def onEvent(evt):

    # ----------- #
    # DIAGNOSTICS #
    # ----------- #
    
    # Spit out a lot for debugging
    if do_diagnostics: diagnostics.diag(evt)

    # Time measurement
    analysis.event.printProcessingRate()

    # -------- #
    # ANALYSIS #
    # -------- #
    
    # HIT FINDING
    # Simple hit finding by counting lit pixels
    analysis.hitfinding.countLitPixels(evt, c2x2_type, c2x2_key, aduThreshold=aduThreshold, hitscoreThreshold=hitscoreThreshold, mask=mask_c2x2)
    hit = evt["analysis"]["isHit - " + c2x2_key]
    
    if not hit:
        # COLLECTING BACKGROUND
        # Update background buffer
        bg.add(c2x2)
        # Write background to file
        bg.write(evt,directory=this_dir+"/stack",interval=Nbg)
    else:
        print "HIT"
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

    if not hit:
        
        pass
    
    else:

        # Send hit info to interface
        plotting.line.plotHistory(hit)
        # Plot MeanMap of hitrate(x,y)
        ### NEED CONF ->
        #x = evt["parameters"]["injector_x"]
        #y = evt["parameters"]["injector_y"]
        #z = hit
        #plotting.correlation.plotMeanMap(x,y,z, plotid='HitrateMeanMap', **hitrateMeanMap)
        #plotting.line.plotHistory(evt["analysis"]["injector_x"])
        #plotting.line.plotHistory(evt["analysis"]["injector_y"])
        #plotting.line.plotHistory(evt["analysis"]["injector_z"])
        ### <- NEED CONF
        # TO DO: injector position x,y,z
        # TO DO: heatmap size injector position
        # TO DO: heatmap intensity injector position
        # if size in range
        # plot image in separate buffer
        # play sound
        # else
        # Plot fit image no success
            
        if do_sizing:
            # Output
            plotting.line.plotHistory(evt["analysis"]["fit error"])

            if fit_succeeded:
                # Plot image
                plotting.image.plotImage(evt[c2x2_type][c2x2_key], msg=hit_msg, log=True, mask=mask_c2x2, name="Fit succeeded")
                # Plot radial average
                plotting.line.plotTrace(evt["analysis"]["radial average - fit"], evt["analysis"]["radial distance - fit"],tracelen=tracelen)           
                # Plot parameter histories
                plotting.line.plotHistory(evt["analysis"]["offCenterX"])
                plotting.line.plotHistory(evt["analysis"]["offCenterY"])
                plotting.line.plotHistory(evt["analysis"]["diameter"])
                plotting.line.plotHistory(evt["analysis"]["intensity"])
                if good_hit:
                    plotting.correlation.plotScatter(evt["analysis"]["diameter"], evt["analysis"]["intensity"], plotid='Diameter vs. intensity', history=100)
            else:
                # Plot image
                plotting.image.plotImage(evt[c2x2_type][c2x2_key], msg=hit_msg, log=True, mask=mask_c2x2, name="Fit failed")
        
        # Plot the glorious shots
        # image
        hit_msg = ""
        plotting.image.plotImage(evt[c2x2_type][c2x2_key], msg=hit_msg, log=True, mask=mask_c2x2)
        # radial average
        plotting.line.plotTrace(evt["analysis"]["radial average - "+c2x2_key], evt["analysis"]["radial distance - "+c2x2_key],tracelen=radial_tracelen)        
