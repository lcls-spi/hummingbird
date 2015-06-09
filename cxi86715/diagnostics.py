

def diag(evt):
    # Print event variables
    print "Native keys: ",      evt.native_keys()
    print "Hummingbird keys: ", evt.keys()
    print "EPICS keys: ",       evt["parameters"].keys()
    print "Detectors: ",        evt["photonPixelDetectors"].keys()
    print "Detectors: ",        evt["calibrated"].keys()

