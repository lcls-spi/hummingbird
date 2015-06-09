

def diag(evt):
    # Print event variables
    try:
        print "Native keys: ",      evt.native_keys()
    except:
        print "WARNING: Cannot find native event keys."
    try:
        print "Hummingbird keys: ", evt.keys()
    except:
        print "WARNING: Cannot find hummingbird keys in event."
    try:
        print "EPICS keys: ",       evt["parameters"].keys()
    except:
        print "WARNING: Cannot find EPICS keys in event."
    try:
        print "Detectors: ",        evt["photonPixelDetectors"].keys()
    except:
        print "WARNING: Cannot find detector keys in event."
    try:
        print "Detectors (calibrated): ",        evt["calibrated"].keys()
    except:
        print "WARNING: Cannot find calibrated detectors keys in event."
    try:
        print "Detectors (image): ",        evt["image"].keys()
    except:
        print "WARNING: Cannot find image detectors keys in event."

