import analysis.event
import analysis.beamline
import analysis.pixel_detector
import analysis.background
import ipc   


state = {
    'Facility': 'LCLS',
    'LCLS/DataSource': 'exp=cxi86715:run=1',
    'LCLS/PsanaConf': 'Ds2.cfg',
    #'LCLS/PsanaConf': 'Dg3.cfg',
}

BG = analysis.background.Stack(name="bg",maxLen=1000)

def onEvent(evt):
    cspad = evt["calibrated"]["CsPad Ds2[calibrated]"]
    analysis.beamline.printPulseEnergy(evt['pulseEnergies'])
    analysis.beamline.printPhotonEnergy(evt['photonEnergies'])
    print "EPICS photon energy = %g eV" %(evt['parameters']['SIOC:SYS0:ML00:AO541'].data)
    analysis.pixel_detector.printStatistics(evt['photonPixelDetectors'])
    analysis.pixel_detector.printStatistics(evt['ionTOFs'])
    analysis.event.printProcessingRate()
    # Update background buffer
    BG.add(cspad.data[0,:,:])
    # Write background to file
    BG.write(evt,directory=".",interval=100)
