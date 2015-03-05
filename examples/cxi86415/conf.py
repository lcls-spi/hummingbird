import time
import analysis.event
import analysis.beamline
import analysis.background
import analysis.pixel_detector

state = {
    'Facility': 'LCLS',

    #'LCLS/DataSource': '/reg/neh/home2/benedikt/data/cxi/cxic9714/xtc/e419-r0199-s09-c00.xtc'
    #'LCLS/DataSource': 'shmem=CXI.0:stop=no',
    'LCLS/DataSource': 'exp=cxi86415:run=2:xtc',
    'LCLS/PsanaConf': 'small_back.cfg',

    'aduThreshold': 0,
    'aduPhoton': 10,

    'meanPhotonMap/initialize': True,
    'meanPhotonMap/paramXmin': -2,
    'meanPhotonMap/paramXmax':  2,
    'meanPhotonMap/paramYmin': -2,
    'meanPhotonMap/paramYmax':  2,
    'meanPhotonMap/paramXbin':  0.01,
    'meanPhotonMap/paramYbin':  0.01,
    'meanPhotonMap/updateRate': 100
}

def onEvent(evt):
    #print evt.nativeKeys()
    #print evt.keys()
    #print evt['parameters'].keys()
    #print evt['calibrated'].keys()
    nrPhotons = analysis.pixel_detector.countNrPhotons(evt['calibrated']['CsPad Dg3 [calibrated]'].data)
    analysis.background.plotMeanPhotonMap(nrPhotons, evt['parameters']['ap1_x'].data, evt['parameters']['ap1_y'].data)
    
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
    analysis.event.printProcessingRate(evt)
    #analysis.pixel_detector.plotImages(evt['reconstructed'])
    #time.sleep(1)
