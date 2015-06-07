"""Configuration for CXI86145"""
import ipc
import time
import analysis.event
import analysis.beamline
import analysis.background
import analysis.hitfinding
import analysis.pixel_detector
import plotting.image
import plotting.line
import plotting.correlation

# Configuration of state
# ----------------------
state = {
    'Facility': 'LCLS',

    #'LCLS/DataSource': 'shmem=4_3_psana_CXI.0:stop=no',
    #'LCLS/DataSource': 'shmem=CXI.0:stop=no',
    'LCLS/DataSource': 'exp=cxi86415:run=19:xtc',

    #'LCLS/PsanaConf': 'Dg3.cfg',
    #'LCLS/PsanaConf': 'Dg3_recons.cfg',
    'LCLS/PsanaConf': 'Ds2.cfg',
    #'LCLS/PsanaConf': 'Ds2_recons.cfg',
    #'LCLS/PsanaConf': 'Ds1.cfg',
    #'LCLS/PsanaConf': 'Ds1_recons.cfg',

    }


# Parameters
# ----------
aduThreshold = 20
aduPhoton    = 1
litPixelThreshold = 200
detectorUpdateRate = 100

# Configuration of plots
# ----------------------
histogram = {
    'hmin': -30,
    'hmax': 70,
    'bins': 100}

meanIntensityAperture1 = {
    'xmin':  2000,
    'xmax':  10000,
    'ymin':  -10000,
    'ymax':  -2000,
    'step':  10,
    'localRadius': 10,
    'overviewStep':100,
    'xlabel': 'position in x [mm]',
    'ylabel': 'position in y [mm]'}

meanIntensityAperture2 = {
    'xmin':  3700-2000,
    'xmax':  3700+2000,
    'ymin':  7000-2000,
    'ymax':  7000+2000,
    'step':  10,
    'localRadius': 100,
    'overviewStep':100,
    'xlabel': 'position in x [mm]',
    'ylabel': 'position in y [mm]'}

meanIntensityAperture2 = {
    'xmin':   4000-2000,
    'xmax':   4000+2000,
    'ymin':   6000-2000,
    'ymax':   6000+2000,
    'step': 1,
    'localRadius': 100,
    'overviewStep':100,
    'xlabel': 'position in x [mm]',
    'ylabel': 'position in y [mm]'}

meanIntensitySample = {
    'xmin': 146-50,
    'xmax': 146+50,
    'ymin': -40-50,
    'ymax': -40+50,
    'step': 0.002,   
    'localRadius':40,
    'overviewStep': 0.5, 
    'xlabel': 'position in x [mm]',
    'ylabel': 'position in y [mm]'}
    
def onEvent(evt):
    #print "Native keys: ",      evt.native_keys()
    #print "Hummingbird keys: ", evt.keys()
    #print "EPICS keys: ",       evt["parameters"].keys()
    #print "Detectors: ",        evt["photonPixelDetectors"].keys()
    #print "Detectors: ",        evt["calibrated"].keys()

    # What detector to use
    try:
        cspad = evt["calibrated"]["CsPad Ds2[calibrated]"]
        #cspad = evt["calibrated"]["CsPad Dg3 [calibrated]"]
        #cspad = evt["reconstructed"]["CsPad Ds2 [reconstructed]"]
    except TypeError:
        print "No detector available"
        return

    # Have a look at the detector to see if everything is alright
    # -----------------------------------------------------------    
    plotting.image.plotImage(cspad)
    
    # Average Pulse Energy
    # --------------------
    #print evt["pulseEnergies"]
    analysis.beamline.averagePulseEnergy(evt, "pulseEnergies")
    for pE in evt["pulseEnergies"].keys(): 
        plotting.line.plotHistory(evt["pulseEnergies"][pE])

    # Get central 4 ASICS of CSPAD Ds2 detector in stack
    # --------------------------------------------------
    analysis.pixel_detector.getCentral4Asics(evt, "calibrated", "CsPad Ds2[calibrated]")

    # Plot Histogram of detector
    # --------------------------
    plotting.line.plotHistogram(evt["analysis"]["central4Asics"], **histogram)


    # Get total nr. of photons on the detector
    # ----------------------------------------
    analysis.pixel_detector.totalNrPhotons(evt, "analysis" , "central4Asics", aduPhoton, aduThreshold)
    plotting.line.plotHistory(evt["analysis"]["nrPhotons - central4Asics"])
    
    # Plotting mean intenisty map for Aperture 1
    # ------------------------------------------
    x,y = evt['parameters']['ap1_x'], evt['parameters']['ap1_y']
    print "Aperture 1, position in x: ", x.data
    print "Aperture 1, position in y: ", y.data
    print "Nr photons: ",  evt["analysis"]["nrPhotons - central4Asics"].data
    print "Average Pulse Energy: ", evt["analysis"]["averagePulseEnergy"].data
    msg_aperture1 = "Pos: (x,y) = (%.2f, %.2f)" %(x.data,y.data)
    plotting.correlation.plotMeanMap(x, y, evt["analysis"]["nrPhotons - central4Asics"], evt["analysis"]["averagePulseEnergy"], msg=msg_aperture1, update=10, **meanIntensityAperture1)
    plotting.line.plotHistory(evt['parameters']['ap1_x'])
    plotting.line.plotHistory(evt['parameters']['ap1_y'])
        
    # Plotting mean intensity map for fixed target sample
    # ---------------------------------------------------
    #x = evt['parameters']['CXI:SC1:MMS:02.RBV']
    #y = evt['parameters']['CXI:USR:MMS:17.RBV']
    #print "Fixed target  position in x: ", x.data
    #print "Fixed target  position in y: ", y.data
    #msg_sample = "Pos: (x,y) = (%.2f, %.2f)" %(x.data,y.data)
    #plotting.correlation.plotMeanMap(x,y, evt["analysis"]["nrPhotons - central4Asics"], evt["analysis"]["averagePulseEnergy"], msg=msg_sample, update=100, **meanIntensitySample)
    #plotting.line.plotHistory(evt['parameters']['CXI:SC1:MMS:02.RBV'])
    #plotting.line.plotHistory(evt['parameters']['CXI:USR:MMS:17.RBV'])
    
    # Hitfinding
    # ----------
    analysis.hitfinding.countLitPixels(evt, 'calibrated', 'CsPad Ds2[calibrated]', aduThreshold, litPixelThreshold)
    plotting.line.plotHistory(evt["analysis"]["hitscore - CsPad Ds2[calibrated]"])
    if evt["analysis"]["isHit - CsPad Ds2[calibrated]"]: 
        plotting.image.plotImage(cspad)

    # How fast are we processing the data?
    # ------------------------------------
    analysis.event.printProcessingRate()
