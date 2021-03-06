from numpy import sum, mean, min, max, std
import ipc
import numpy as np
from backend import ureg
from backend import add_record
import utils.array

def printStatistics(detectors):
    for k,r in detectors.iteritems():
        v = r.data
        print "%s (%s): sum=%g mean=%g min=%g max=%g std=%g" % (k, r.unit.units,
                                                                sum(v), mean(v),
                                                                min(v), max(v),
                                                                std(v))

def getSubsetAsics(evt, type, key, subset, output):
    """Adds a one-dimensional stack of an arbitrary subset of asics
    to ``evt["analysis"][output]``.

    Args:
        :evt:       The event variable
        :type(str): The event type (e.g. photonPixelDetectors)
        :key(str):  The event key (e.g. CCD)
        :subset(list): Asic indices
        :output: The output key in analysis

    :Authors:
        Carl Nettelblad (carl.nettelblad@it.uu.se)
        Benedikt J. Daurer (benedikt@xray.bmc.uu.se)
    """
    stack = []
    detector = evt[type][key]
    for i in subset:
        panel = i / 2
        asic = i % 2
        stack.append(detector.data[panel,:,(asic*194):((asic+1)*194)])
    add_record(evt["analysis"], "analysis", output, np.hstack(stack), detector.unit)

def getCentral4Asics(evt, type, key):
    """Adds a one-dimensional stack of its 4 centermost asics
    to ``evt["analysis"]["central4Asics"]``.

    Args:
        :evt:       The event variable
        :type(str): The event type (e.g. photonPixelDetectors)
        :key(str):  The event key (e.g. CCD)

    :Authors:
        Carl Nettelblad (carl.nettelblad@it.uu.se)
        Benedikt J. Daurer (benedikt@xray.bmc.uu.se)
    """
    getSubsetAsics(evt, type, key, map(lambda i : (i * 8 + 1) * 2, xrange(4)), "central4Asics")

    
def totalNrPhotons(evt, type, key, aduPhoton=1, aduThreshold=0.5):
    """Estimates the total nr. of photons on the detector and adds it to ``evt["analysis"]["nrPhotons - " + key]``.

    Args:
        :evt:       The event variable
        :type(str): The event type (e.g. photonPixelDetectors)
        :key(str):  The event key (e.g. CCD)

    Kwargs:
        :aduPhoton(int):    ADU count per photon, default = 1
        :aduThreshold(int): only pixels above this threshold given in units of ADUs are valid, default = 0.5
    
    :Authors:
        Benedikt J. Daurer (benedikt@xray.bmc.uu.se)
    """
    data  = evt[type][key].data.flat
    valid = data > aduThreshold
    add_record(evt["analysis"], "analysis", "nrPhotons - " + key, sum(data[valid]) / float(aduPhoton))

initialized = {}
def assemble(evt, type, key, x, y, nx=None, ny=None, subset=None, outkey=None):
    """Asesembles a detector image given some geometry and adds assembled image to ``evt["analysis"]["assembled - " + key]``.

    Args:
        :evt:        The event variable
        :type(str):  The event type (e.g. photonPixelDetectors)
        :key(str):   The event key (e.g. CCD)
        :x(int ndarray): X coordinates
        :y(int ndarray): Y coordinates

    Kwargs:
        :nx(int):    Total width of assembled image (zero padding)
        :ny(int):    Total height of assembled image (zero padding)

    :Authors:
        Benedikt J. Daurer (benedikt@xray.bmc.uu.se)
    """
    if not key in initialized:
        if subset is not None:
            x_ss = []
            y_ss = []
            for i in subset:
                panel = i / 2
                asic = i % 2
                x_ss.append(x[panel,:,(asic*194):((asic+1)*194)])
                y_ss.append(y[panel,:,(asic*194):((asic+1)*194)])
            x_ss = np.hstack(x_ss)
            y_ss = np.hstack(y_ss)
        else:
            x_ss = x
            y_ss = y
        assembled, height, width, shape, y_ss, x_ss = utils.array.assembleImage(x_ss, y_ss ,nx=nx, ny=ny, return_indices=True)
        initialized[key] = {
            'assembled':assembled,
            'height':height,
            'width':width,
            'shape':shape,
            'y':y_ss,
            'x':x_ss
        }
    assembled = initialized[key]['assembled']
    height = initialized[key]['height']
    width = initialized[key]['width']
    shape = initialized[key]['shape']
    y = initialized[key]['y']
    x = initialized[key]['x']
    if subset is not None:
        data = []
        for i in subset:
            panel = i / 2
            asic = i % 2
            data.append(evt[type][key].data[panel,:,(asic*194):((asic+1)*194)])
        data = np.hstack(data)
    else:
        data = evt[type][key].data
    assembled[height-shape[0]:, :shape[1]][y,x] = data
    if outkey is None:
        add_record(evt["analysis"], "analysis", "assembled - "+key, assembled)
    else:
        add_record(evt["analysis"], "analysis", outkey, assembled)



    
def bin(evt, type, key, binning, mask=None):
    """Bin a detector image given a binning factor (and mask) to ``evt["analysis"]["binned image - " + key]`` (``evt["analysis"]["binned mask - " + key]``

    Args:
        :evt:        The event variable
        :type(str):  The event type (e.g. photonPixelDetectors)
        :key(str):   The event key (e.g. CCD)
        :binning(int):   The linear binning factor

    Kwargs:
        :mask:    Binary mask, pixels that are masked out are not counted into the binned value.

    :Authors:
        Max F. Hantke (hantke@xray.bmc.uu.se)
    """
    import spimage
    image = evt[type][key].data
    binned_image, binned_mask = spimage.binImage(image, binning, msk=mask, output_binned_mask=True)
    add_record(evt["analysis"], "analysis", "binned image - "+key, binned_image)
    if binned_mask is not None:
        add_record(evt["analysis"], "analysis", "binned mask - "+key, binned_mask)

def radial(evt, type, key, mask=None, cx=None, cy=None):
    """Compute the radial average of a detector image given the center position (and a mask) and saves it to ``evt["analysis"]["radial average - " + key]`` and the radial distances are saved to``evt["analysis"]["radial distance - " + key]``

    Args:
        :evt:        The event variable
        :type(str):  The event type (e.g. photonPixelDetectors)
        :key(str):   The event key (e.g. CCD)

    Kwargs:
        :mask:    Binary mask, pixels that are masked out are not counted into the radial average.
        :cx(float):  X-coordinate of the center position. If None the center will be in the middle.
        :cy(float):  Y-coordinate of the center position. If None the center will be in the middle.

    :Authors:
        Max F. Hantke (hantke@xray.bmc.uu.se)
    """
    import spimage
    image = evt[type][key].data
    r, img_r = spimage.radialMeanImage(image, msk=mask, cx=cx, cy=cy, output_r=True)
    valid = np.isfinite(img_r)
    if valid.sum() > 0:
        r = r[valid]
        img_r = img_r[valid]
    add_record(evt["analysis"], "analysis", "radial distance - "+key, r)
    add_record(evt["analysis"], "analysis", "radial average - "+key, img_r)


    
def cmc(evt, type, key, mask=None):
    """ Common mode subtraction with median value from pixels within given mask. Add record ``evt["analysis"]["cmc - " + key]``

    Args:
      :evt:        The event variable
      :type(str):  The event type (e.g. photonPixelDetectors)
      :key(str):   The event key (e.g. CCD)

    Kwargs:
      :mask: Binary mask
    
    :Authors:
        Max F. Hantke (hantke@xray.bmc.uu.se)
    """
    data = evt[type][key].data
    dataCorrected = utils.array.cmc(data, mask=mask)
    add_record(evt["analysis"], "analysis", "cmc - " + key, dataCorrected)

def cmc_pnccd(evt, type, key):
    try:
        data = evt[type][key].data
    except:
        print "NO DATA!"
        return
    if data is None:
        return
    dataCorrected = utils.array.cmc_pnccd(data)
    add_record(evt["analysis"], "analysis", "cmc_pnccd - " + key, dataCorrected)

def bgsub(evt, type, key, bg):
    data = evt[type][key].data
    if bg is not None:
        dataCorrected = data - bg
    else:
        dataCorrected = data
    add_record(evt["analysis"], "analysis", "bgsub - " + key, dataCorrected)
