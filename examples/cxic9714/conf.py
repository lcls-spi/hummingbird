import time
import analysis.event
import analysis.beamline
import analysis.pixel_detector

state = {
    'Facility': 'LCLS',
    #'LCLS/DataSource': '/data/rawdata/LCLS/cxi/cxic9714/xtc/e419-r0263-s03-c00.xtc'
#    'LCLS/DataSource': 'exp=cxic9714:run=199:xtc',
    'LCLS/DataSource': '/reg/neh/home/benedikt/data/cxi/cxic9714/xtc/e419-r0199-s09-c00.xtc',
    'LCLS/PsanaConf': 'psana.conf'
}

def onEvent(evt):
    analysis.event.printNativeKeys(evt)
#    analysis.beamline.plotPulseEnergy(evt['pulseEnergies'])
#    analysis.beamline.printPulseEnergy(evt['pulseEnergies'])
#    analysis.beamline.printPhotonEnergy(evt['photonEnergies'])
#    print "EPICS photon energy = %g eV" %(evt['parameters']['SIOC:SYS0:ML00:AO541'].data)
    analysis.pixel_detector.printStatistics(evt['photonPixelDetectors'])
    analysis.pixel_detector.plotImages(evt['photonPixelDetectors'])
#    analysis.pixel_detector.printStatistics(evt['ionTOFs'])
#    analysis.event.printID(evt['eventID'])
#    analysis.event.plotFiducial(evt['eventID'])
    analysis.event.printProcessingRate(evt)
    time.sleep(1)
