"""Configuration for CXI86145"""
import ipc
import time
import analysis.event
import analysis.beamline
import analysis.background
import analysis.hitfinding
import analysis.pixel_detector
import plotting.maps

# Configuration of state
# ----------------------
state = {
    'Facility': 'LCLS',

    #'LCLS/DataSource': 'shmem=4_3_psana_CXI.0:stop=no',
    'LCLS/DataSource': 'shmem=CXI.0:stop=no',
    #'LCLS/DataSource': 'exp=cxi86415:run=17:xtc',

    #'LCLS/PsanaConf': 'Dg3.cfg',
    #'LCLS/PsanaConf': 'Dg3_recons.cfg',
    'LCLS/PsanaConf': 'Ds2.cfg',
    #'LCLS/PsanaConf': 'Ds2_recons.cfg',
    #'LCLS/PsanaConf': 'Ds1.cfg',
    #'LCLS/PsanaConf': 'Ds1_recons.cfg',

    'aduThreshold': 20,
    'aduPhoton': 1,
    'hitscoreMinCount':200,

    'detectorUpdateRate':100,

    }

# Configuration of plots
# ----------------------
histogram = {
    'hmin': -30,
    'hmax': 70,
    'bins': 100}

meanIntensityAperture1 = {
    'xmin':  8000-2000,
    'xmax':  8000+2000,
    'ymin':  -1500-2000,
    'ymax':  -1500+2000,
    'step':  10,
    'localRadius': 100,
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
    
#if ipc.mpi.rank > 5:
#    state['LCLS/DataSource'] = 'shmem=0_42_psana_CXI.0:stop=no'

def onEvent(evt):
    #print "Native keys: ",      evt.nativeKeys()
    #print "Hummingbird keys: ", evt.keys()
    #print "EPICS keys: ",       evt["parameters"].keys()
    #print "Detectors: ",        evt["photonPixelDetectors"].keys()

    # What detector to use
    try:
        cspad = evt["calibrated"]["CsPad Ds2 [calibrated]"]
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
    evt["pulseEnergies"]["average"] = analysis.beamline.averagePulseEnergy(evt["pulseEnergies"])
    for pE in evt["pulseEnergies"]: plotting.line.plotHistory(pE)

    # Get central 4 ASICS of CSPAD Ds2 detector in stack
    # --------------------------------------------------
    evt["central4Asicis"] = analysis.pixel_detector.getCentral4Asics(cspad)

    # Plot Histogram of detector
    # --------------------------
    plotting.line.plotHistogram(evt["central4Asics"], **histogram)


    # Get total nr. of photons on the detector
    # ----------------------------------------
    evt["nrPhotons"] = analysis.pixel_detector.totalNrPhotons(evt["central4Asics"], aduPhoton=state["aduPhoton"], aduThreshold=state["aduThreshold"])
    plotting.line.plotHistory(evt["nrPhotons"])
    
    # Plotting mean intenisty map for Aperture 1
    # ------------------------------------------
    x,y = evt['parameters']['ap1_x'].data, evt['parameters']['ap1_y'].data 
    print "Aperture 1, position in x: ", x
    print "Aperture 1, position in y: ", y
    msg_aperture1 = "Pos: (x,y) = (%.2f, %.2f)" %(x,y)
    plotting.maps.plotMeanMap('aperture1', evt['parameters']['ap1_x'], evt['parameters']['ap1_y'], evt["nrPhotons"], evt["pulseEnergies"]["average"], msg=msg_aperture1, update=100, **meanIntensityAperture1)
    #analysis.background.plotAperturePos(evt['parameters']['ap1_x'])
    #analysis.background.plotAperturePos(evt['parameters']['ap1_y'])

    # Plotting mean intenisty map for Aperture 2
    # ------------------------------------------
    x,y = evt['parameters']['ap2_x'].data, evt['parameters']['ap2_y'].data 
    print "Aperture 2, position in x: ", x
    print "Aperture 2, position in y: ", y
    msg_aperture2 = "Pos: (x,y) = (%.2f, %.2f)" %(x,y)
    plotting.maps.plotMeanMap('aperture2', evt['parameters']['ap2_x'], evt['parameters']['ap2_y'], evt["nrPhotons"], evt["pulseEnergies"]["average"], msg=msg_aperture3, update=100, **meanIntensityAperture3)
    #analysis.background.plotAperturePos(evt['parameters']['ap2_x'])
    #analysis.background.plotAperturePos(evt['parameters']['ap2_y'])

    # Plotting mean intenisty map for Aperture 3
    # ------------------------------------------
    x,y = evt['parameters']['ap3_x'].data, evt['parameters']['ap2_y'].data 
    print "Aperture 3, position in x: ", x
    print "Aperture 3, position in y: ", y
    msg_aperture3 = "Pos: (x,y) = (%.2f, %.2f)" %(x,y)
    plotting.maps.plotMeanMap('aperture3', evt['parameters']['ap3_x'], evt['parameters']['ap3_y'], evt["totalIntensity"], evt["pulseEnergy"], msg=msg_aperture3, update=100, **meanIntensityAperture3)
    #analysis.background.plotAperturePos(evt['parameters']['ap3_x'])
    #analysis.background.plotAperturePos(evt['parameters']['ap3_y'])
        
    # Plotting mean intensity map for fixed target sample
    # ---------------------------------------------------
    x,y = evt['parameters']['CXI:SC1:MMS:02.RBV'].data, evt['parameters']['CXI:USR:MMS:17.RBV'].data
    print "Fixed target  position in x: ", x
    print "Fixed target  position in y: ", y
    msg_sample = "Pos: (x,y) = (%.2f, %.2f)" %(x,y)
    plotting.maps.plotMeanMap('sample', evt['parameters']['CXI:SC1:MMS:02.RBV'], evt['parameters']['CXI:USR:MMS:17.RBV'], evt["nrPhotons"], evt["pulseEnergies"]["average"], msg=msg_sample, update=100, **meanIntensitySample)
    #analysis.background.plotAperturePos(evt['parameters']['CXI:SC1:MMS:02.RBV'])
    #analysis.background.plotAperturePos(evt['parameters']['CXI:USR:MMS:17.RBV'])
    
    # Hitfinding
    # ----------
    hit, evt["hitscore"] = analysis.hitfinding.countLitPixels(evt['calibrated']['CsPad Dg3 [calibrated]'], aduThreshold, litPixelThreshold)
    plotting.line.plotHistory(evt["hitscore"])
    if hit: plotting.image.plotImage(cspad)

    # How fast are we processing the data?
    # ------------------------------------
    analysis.event.printProcessingRate(evt)
