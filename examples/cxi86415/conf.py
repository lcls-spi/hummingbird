
import time
import analysis.event
import analysis.beamline
import analysis.background
import analysis.hitfinding
import analysis.pixel_detector

state = {
    'Facility': 'LCLS',

    'LCLS/DataSource': 'shmem=CXI.0:stop=no',
    #'LCLS/DataSource': 'exp=cxi86415:run=2:xtc',
    'LCLS/PsanaConf': 'small_back.cfg',

    'aduThreshold': 20,
    'aduPhoton': 1,
    'hitscoreMinCount':200,

    'detectorUpdateRate':100,

    'meanPhotonMap': {
        'aperture1': {
            'paramXmin': -10000,
            'paramXmax':  10000,
            'paramYmin': -10000,
            'paramYmax':  10000,
            'paramXbin':  100,
            'paramYbin':  100,
            'updateRate': 100
            },
        'aperture2': {
            'paramXmin': -10000,
            'paramXmax':  10000,
            'paramYmin': -10000,
            'paramYmax':  10000,
            'paramXbin':  100,
            'paramYbin':  100,
            'updateRate': 100
            },
        'aperture3': {
            'paramXmin': -10000,
            'paramXmax':  10000,
            'paramYmin': -10000,
            'paramYmax':  10000,
            'paramXbin':  100,
            'paramYbin':  100,
            'updateRate': 100
            }
        }
    }

def onEvent(evt):
    #print "Native keys: ", evt.nativeKeys()
    #print "Hummingbird keys: ", evt.keys()
    #print "EPICS keys: ", evt["parameters"].keys()

    # Detector calibration and other stuff
    #analysis.pixel_detector.plotDetector(evt['calibrated']['CsPad Dg3 [calibrated]'])

    # Pulse energies
    #print evt["pulseEnergies"]
    analysis.beamline.plotPulseEnergy(evt["pulseEnergies"])
    pulseEnergy = analysis.beamline.averagePulseEnergies(evt["pulseEnergies"])

    # Counting photons on the small back detector
    nrPhotons = analysis.pixel_detector.countNrPhotons(evt['calibrated']['CsPad Dg3 [calibrated]'])
    analysis.pixel_detector.plotNrPhotons("CsPad2x2 - Nr. of Photons (adup = %d, th = %d)" %(state["aduPhoton"], state["aduThreshold"]), nrPhotons)

    # Mean Photon Map for Alignment of Aperture 1
    #print "Aperture 1, position in x: ", evt['parameters']['ap1_x'].data
    #print "Aperture 1, position in y: ", evt['parameters']['ap1_y'].data
    analysis.background.plotMeanPhotonMap('aperture1', state["meanPhotonMap"]["aperture1"], nrPhotons, evt['parameters']['ap1_x'], evt['parameters']['ap1_y'], pulseEnergy)
    analysis.background.plotAperturePos(evt['parameters']['ap1_x'])
    analysis.background.plotAperturePos(evt['parameters']['ap1_y'])

    # Mean Photon Map for Alignment of Aperture 3
    #print "Aperture 2, position in x: ", evt['parameters']['ap2_x'].data
    #print "Aperture 2, position in y: ", evt['parameters']['ap2_y'].data
    analysis.background.plotMeanPhotonMap('aperture2', state["meanPhotonMap"]["aperture2"], nrPhotons, evt['parameters']['ap2_x'], evt['parameters']['ap2_y'], pulseEnergy)
    analysis.background.plotAperturePos(evt['parameters']['ap2_x'])
    analysis.background.plotAperturePos(evt['parameters']['ap2_y'])
    
    # Mean Photon Map for Alignment of Aperture 3
    #print "Aperture 3, position in x: ", evt['parameters']['ap3_x'].data
    #print "Aperture 3, position in y: ", evt['parameters']['ap3_y'].data
    analysis.background.plotMeanPhotonMap('aperture3', state["meanPhotonMap"]["aperture3"], nrPhotons, evt['parameters']['ap3_x'], evt['parameters']['ap3_y'], pulseEnergy)
    analysis.background.plotAperturePos(evt['parameters']['ap3_x'])
    analysis.background.plotAperturePos(evt['parameters']['ap3_y'])

    # Hitfinding
    hit, hitscore = analysis.hitfinding.countLitPixels(evt['calibrated']['CsPad Dg3 [calibrated]'])
    analysis.hitfinding.plotHitscore(hitscore)

    # How fast are we processing the data?
    analysis.event.printProcessingRate(evt)
