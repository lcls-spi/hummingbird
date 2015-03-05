
import time
import analysis.event
import analysis.beamline
import analysis.background
import analysis.pixel_detector

state = {
    'Facility': 'LCLS',

    'LCLS/DataSource': 'shmem=CXI.0:stop=no',
    #'LCLS/DataSource': 'exp=cxi86415:run=2:xtc',
    'LCLS/PsanaConf': 'small_back.cfg',

    'aduThreshold': 15,
    'aduPhoton': 20,

    'meanPhotonMap': {
        'aperture1': {
            'paramXmin': 0,
            'paramXmax': 1000,
            'paramYmin': -20000,
            'paramYmax': -15000,
            'paramXbin': 10,
            'paramYbin': 10,
            'updateRate': 100
            },
        'aperture2': {
            'paramXmin': 0,
            'paramXmax': 1000,
            'paramYmin': -20000,
            'paramYmax': -15000,
            'paramXbin': 10,
            'paramYbin': 10,
            'updateRate': 100
            },
        'aperture3': {
            'paramXmin': 0,
            'paramXmax': 1000,
            'paramYmin': -20000,
            'paramYmax': -15000,
            'paramXbin': 10,
            'paramYbin': 10,
            'updateRate': 100
            }
        }
    }

def onEvent(evt):
    #print "Native keys: ", evt.nativeKeys()
    #print "Hummingbird keys: ", evt.keys()

    # Detector calibration and other stuff
    analysis.pixel_detector.plotDetector(evt['calibrated']['CsPad Dg3 [calibrated]'])

    # Counting photons on the small back detector
    nrPhotons = analysis.pixel_detector.countNrPhotons(evt['calibrated']['CsPad Dg3 [calibrated]'])

    # Mean Photon Map for Alignment of Aperture 1
    print "Aperture 1, position in x: ", evt['parameters']['ap1_x'].data
    print "Aperture 1, position in y: ", evt['parameters']['ap1_y'].data
    analysis.background.plotMeanPhotonMap('aperture1', state["meanPhotonMap"]["aperture1"], nrPhotons, evt['parameters']['ap1_x'], evt['parameters']['ap1_y'])

    # Mean Photon Map for Alignment of Aperture 3
    print "Aperture 2, position in x: ", evt['parameters']['ap2_x'].data
    print "Aperture 2, position in y: ", evt['parameters']['ap2_y'].data
    analysis.background.plotMeanPhotonMap('aperture2', state["meanPhotonMap"]["aperture2"], nrPhotons, evt['parameters']['ap2_x'], evt['parameters']['ap2_y'])
    
    # Mean Photon Map for Alignment of Aperture 3
    print "Aperture 3, position in x: ", evt['parameters']['ap3_x'].data
    print "Aperture 3, position in y: ", evt['parameters']['ap3_y'].data
    analysis.background.plotMeanPhotonMap('aperture3', state["meanPhotonMap"]["aperture3"], nrPhotons, evt['parameters']['ap3_x'], evt['parameters']['ap3_y'])
    
    # How fast are we processing the data?
    analysis.event.printProcessingRate(evt)

    #print evt.keys()
    #print evt['photonPixelDetectors'].keys()
    #analysis.beamline.plotPulseEnergy(evt['pulseEnergies'])
#    analysis.beamline.printPulseEnergy(evt['pulseEnergies'])
#    analysis.beamline.printPhotonEnergy(evt['photonEnergies'])
#    print "EPICS photon energy = %g eV" %(evt['parameters']['SIOC:SYS0:ML00:AO541'].data)
#    analysis.pixel_detector.printStatistics(evt['photonPixelDetectors'])
#    analysis.pixel_detector.printStatistics(evt['ionTOFs'])
#    analysis.event.printID(evt['eventID'])
    #analysis.event.plotFiducial(evt['eventID'])

    #analysis.pixel_detector.plotImages(evt['reconstructed'])
    #time.sleep(1)
