import time
import analysis.event
import analysis.beamline
import analysis.pixel_detector

state = {
    'Facility': 'LCLS',
    'LCLS/DataSource': '/home/benedikt//data/e419-r0199-s80-c00.xtc'
}

def onEvent(evt):
    analysis.beamline.plotPulseEnergy(evt['pulseEnergies'])
#    analysis.beamline.printPulseEnergy(evt['pulseEnergies'])
#    analysis.beamline.printPhotonEnergy(evt['photonEnergies'])
#    print "EPICS photon energy = %g eV" %(evt['parameters']['SIOC:SYS0:ML00:AO541'].data)
#    analysis.pixel_detector.printStatistics(evt['photonPixelDetectors'])
#    analysis.pixel_detector.printStatistics(evt['ionTOFs'])
#    analysis.event.printID(evt['eventID'])
#    analysis.event.plotFiducial(evt['eventID'])
    lanalysis.event.printProcessingRate(evt)
    time.sleep(1)
