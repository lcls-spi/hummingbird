

def initial_diagnostics(evt):
    # Print event variables
    try:
        print "Native keys: ",      evt.native_keys()
    except:
        print "WARNING: Cannot find native event keys."
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

def final_diagnostics(evt):
    try:
        print "Hummingbird keys: ", evt.keys()
    except:
        print "WARNING: Cannot find hummingbird keys in event."

    #plotting.line.plotHistogram(evt[c2x2_type][c2x2_key], hmin=-49, hmax=50, bins=100, label='', density=False, history=100)
