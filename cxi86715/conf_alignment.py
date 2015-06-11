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
import utils.array
this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(this_dir)
import diagnostics

# ---------------------------------------------------------
# P S A N A
# ---------------------------------------------------------
state = {}
state['Facility'] = 'LCLS'
do_diagnostics    = False
import getpass
if getpass.getuser() == "cxiopr":
    state['LCLS/DataSource'] = 'shmem=psana.0:stop=no'
else:
    state['LCLS/DataSource'] = 'exp=cxi86715:run=14'

# CSPAD 2x2
# ---------
c2x2_type = "image"
c2x2_key  = "CsPad Dg2[image]"

# CSPAD large
# -----------
clarge_type = "photons"
clarge_key  = "CsPad Ds2[%s]" % clarge_type

# ALIGMENT MOTORS
# ---------------
alignment_x_key = "CXI:SC2:MZM:01"
alignment_y_key = "CXI:SC2:MZM:02"

# Mask
# ----
M_back    = utils.reader.MaskReader(this_dir + "/mask/mask_back.h5","/data/data")
mask_c2x2 = M_back.boolean_mask
(ny_c2x2,nx_c2x2) = mask_c2x2.shape

# ---------------------------------------------------------
# E V E N T   C A L L
# ---------------------------------------------------------

def onEvent(evt):

    # ------------------- #
    # INITIAL DIAGNOSTICS #
    # ------------------- #

    # Time measurement
    analysis.event.printProcessingRate()

    # Send Fiducials and Timestamp
    plotting.line.plotTimestamp(evt["eventID"]["Timestamp"])
    
    # Spit out a lot for debugging
    if do_diagnostics: diagnostics.initial_diagnostics(evt)
    
    # -------- #
    # ANALYSIS #
    # -------- #

    # AVERAGE PULSE ENERGY
    analysis.beamline.averagePulseEnergy(evt, "pulseEnergies")

    # CENTRAL ASICS OF FRONT DETECTOR
    analysis.pixel_detector.getCentral4Asics(evt, clarge_key, clarge_type)

    # COUNT PHOTONS
    analysis.pixel_detector.totalNrPhotons(evt, "analysis", "central4Asics", aduPhoton=1, aduThreshold=0.5)
    analysis.pixel_detector.totalNrPhotons(evt, c2x2_type, c2x2_key, aduPhoton=1, aduThreshold=0.5)
                   
    # ------------------------ #
    # SEND RESULT TO INTERFACE #
    # ------------------------ #

    # Pulse Energy
    plotting.line.plotHistory(evt["analysis"]["averagePulseEnergy"])
    
    # Aperture position
    x = evt["parameters"][aperture_x_key]
    y = evt["parameters"][aperture_y_key]
    plotting.line.plotHistory(x)
    plotting.line.plotHistory(y)

    # Nr. of photons 
    plotting.line.plotHistory(evt["analysis"]["nrPhotons - " + c2x2_key])
    plotting.line.plotHistory(evt["analysis"]["nrPhotons - central4Asics"])
     

    # Plot MeanMap of Nr. of photons (x,y)
    heat = evt["analysis"]["nrPhotons - " + c2x2_key].data
    plotting.correlation.plotMeanMap(x,y, heat, plotid='meanMap', **meanMapParams)

    # Image of back
    plotting.image.plotImage(evt[c2x2_type][c2x2_key], msg="", mask=mask_c2x2, name="Cspad 140k", vmin=vmin_c2x2, vmax=vmax_c2x2)
        
    # ----------------- #
    # FINAL DIAGNOSTICS #
    # ----------------- #
    
    # Spit out a lot for debugging
    if do_diagnostics: diagnostics.final_diagnostics(evt)

