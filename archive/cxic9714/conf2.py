import os
import time
import numpy,collections
import utils.reader
import utils.array
import simulation.cxi
import analysis.event
import analysis.pixel_detector
import analysis.hitfinding
import analysis.sizing
import plotting.line
import plotting.image
import plotting.correlation
import ipc

key_to_data = "entry_1/image_1/data"
key_to_pulse_energy = "LCLS/f_11_ENRC"
key_to_injection = "entry_1/sample_1/geometry_1/translation"
sim = simulation.cxi.Simulation(os.environ["CXIDATA"],
                                key_to_data, 
                                key_to_pulse_energy,
                                key_to_injection)

state = {
    'Facility': 'Dummy',

    'Dummy': {
        'Repetition Rate' : 120,
        'Simulation': sim,
        'Data Sources': {
            'CCD': {
                'data': sim.get_pattern,
                'unit': '',
                'type': 'photonPixelDetectors'
            },
            'pulseEnergy': {
                'data': sim.get_pulse_energy,
                'unit': 'J',
                'type': 'pulseEnergies'
            },
            'injector_posx': {
                'data': sim.get_injector_pos_x,
                'unit': 'um',
                'type': 'parameters'
            },
            'injector_posz': {
                'data': sim.get_injector_pos_z,
                'unit': 'um',
                'type': 'parameters'
            }

        }        
    }
}


# Configure plots
# ---------------
histogramCCD = {
    'hmin': -1,
    'hmax': 19,
    'bins': 100,
    'label': "Nr of photons",
    'history': 50}

heatmapInjector = {
    'xmin': 0,
    'xmax': 10,
    'xbins': 20,
    'ymin': 20,
    'ymax': 120,
    'ybins': 50}

heatmapCenterPos = {
    'xmin': -30,
    'xmax':  10,
    'xbins': 20,
    'ymin': -25,
    'ymax': 15,
    'ybins': 20}

# Mode and binning
# ----------------
#mode = "default"
mode = "radial"
#mode = "default"
binning = 1
if mode == "bin":
    binning = 4

# Model parameters for sphere
# ---------------------------
modelParams = {
    'wavelength':0.1907,
    'pixelsize':110*binning,
    'distance':2400,
    'adu_per_photon':26,
    'quantum_efficiency':1.,
    'material':'virus'}

# Sizing parameters
# -----------------
sizingParams = {
    'd0':100,
    'i0':1,
    'mask_radius':300/binning,
    'brute_evals':40,
    'photon_counting':True}

# Geometry and mask
this_dir = os.path.dirname(os.path.realpath(__file__))
greader = utils.reader.GeometryReader(this_dir + "/geometry.h5")
mreader = utils.reader.MaskReader(this_dir + "/mask.h5","/data/data")
mask    = utils.array.assembleImage(greader.x, greader.y, mreader.boolean_mask, nx=414, ny=414, dtype='bool')

# Background buffer
iD = 0
nD = 100
D = collections.deque(maxlen=nD)
bg = None


def onEvent(evt):

    # Processing rate
    analysis.event.printProcessingRate()

    # Detector statistics
    analysis.pixel_detector.printStatistics(evt["photonPixelDetectors"])

    # Count Nr. of Photons
    analysis.pixel_detector.totalNrPhotons(evt,"photonPixelDetectors", "CCD")
    plotting.line.plotHistory(evt["analysis"]["nrPhotons - CCD"], label='Nr of photons / frame', history=50)

    # Simple hitfinding (Count Nr. of lit pixels)
    analysis.hitfinding.countLitPixels(evt, "photonPixelDetectors", "CCD", aduThreshold=25, hitscoreThreshold=1000, mask=mask)

    # Compute the hitrate
    analysis.hitfinding.hitrate(evt, evt["analysis"]["isHit - CCD"], history=10000)
    
    # Plot the hitscore
    plotting.line.plotHistory(evt["analysis"]["hitscore - CCD"], label='Nr. of lit pixels')

    # Plot the hitrate
    plotting.line.plotHistory(evt["analysis"]["hitrate"], label='Hit rate [%]')

    # Plot injector position in x
    plotting.line.plotHistory(evt["parameters"]["injector_posx"], label='Position in X [um]')

    # Plot injector position in y
    plotting.line.plotHistory(evt["parameters"]["injector_posz"], label='Position in Z [um]')
    
    # Perform sizing on hits
    if not evt["analysis"]["isHit - CCD"]:
        D.append(evt["photonPixelDetectors"]["CCD"].data)
        global iD
        global nD
        global bg
        iD += 1
        if (iD % nD) == 0:
            print "Calculating new background average."
            bg = numpy.array(D).mean(axis=0)
            ipc.new_data("background average", bg)
    else:

        print "It's a hit"

        if mode in ["default", "radial"]:
            ccd_type = "photonPixelDetectors"
            ccd_key = "CCD"
            m = mask
        elif mode == "bin":
            t0 = time.time()
            analysis.pixel_detector.bin(evt, "photonPixelDetectors", "CCD", binning, mask=mask)
            t_bin = time.time() - t0
            binnedMask = evt["analysis"]["binned mask - CCD"].data
            ccd_type = "analysis"
            ccd_key = "binned image - CCD"
            m = binnedMask
                           
        t0 = time.time()
        # Find the center of diffraction
        analysis.sizing.findCenter(evt, ccd_type, ccd_key, mask=m, maxshift=40/binning, threshold=13, blur=4)
        t_center = time.time()-t0

        if mode in ["default","bin"]:
            # Fitting sphere model to get size and intensity
            t0 = time.time()
            analysis.sizing.fitSphere(evt, ccd_type, ccd_key, mask=m, **dict(modelParams, **sizingParams))
            t_size = time.time()-t0
        elif mode == "radial":
            # Calculate radial average
            t0 = time.time()
            cx = evt["analysis"]["offCenterX"].data + (sim.nx - 1) / 2.
            cy = evt["analysis"]["offCenterY"].data + (sim.ny - 1) / 2.
            analysis.pixel_detector.radial(evt, ccd_type, ccd_key, mask=m, cx=cx, cy=cy)          
            # Fitting sphere model to get size and intensity
            analysis.sizing.fitSphereRadial(evt, "analysis", "radial distance - CCD", "radial average - CCD", **dict(modelParams, **sizingParams))
            t_size = time.time()-t0
            
        # Fitting model
        analysis.sizing.sphereModel(evt, "analysis", "offCenterX", "offCenterY", "diameter", "intensity", m.shape, poisson=True, **modelParams)

        if mode == "radial":
            analysis.pixel_detector.radial(evt, "analysis", "fit", mask=m, cx=cx, cy=cy)          
            # 1D arrays have to have same length, otherwise histoty keeping gets messed up
            rlen = 100
            ipc.new_data("radial fit", numpy.array([evt["analysis"]["radial distance - fit"].data.ravel()[:rlen], evt["analysis"]["radial average - fit"].data.ravel()[:rlen]], copy=False))
            ipc.new_data("radial CCD", numpy.array([evt["analysis"]["radial distance - CCD"].data.ravel()[:rlen], evt["analysis"]["radial average - CCD"].data.ravel()[:rlen]], copy=False))
            
        t_all = t_center + t_size
        print "Time: %e sec (center / size : %.2f%% / %.2f%%)" % (t_all, 100.*t_center/t_all, 100.*t_size/t_all)

        # Error parameter
        diff = (evt[ccd_type][ccd_key].data-evt["analysis"]["fit"].data)[m].sum()/float(evt[ccd_type][ccd_key].data[m].sum())
        ipc.new_data("fit diff", diff)
        
        plotting.line.plotHistory(evt["analysis"]["offCenterX"])
        plotting.line.plotHistory(evt["analysis"]["offCenterY"])
        plotting.line.plotHistory(evt["analysis"]["diameter"])
        plotting.line.plotHistory(evt["analysis"]["intensity"])
        plotting.line.plotHistory(evt["analysis"]["error"])

        # Attach a message to the plots
        s0 = evt["analysis"]["diameter"].data
        I0 = evt["analysis"]["intensity"].data
        msg_glo = "diameter = %.2f nm, \nintensity = %.2f mJ/um2" % (s0, I0)
        msg_fit = "Fit result: \ndiameter = %.2f nm, \nintensity = %.2f mJ/um2, diff=%f" % (s0, I0, diff)

        # Plot the glorious shots
        plotting.image.plotImage(evt[ccd_type][ccd_key], msg=msg_glo, log=True, mask=m)
        
        # Plot the fitted model
        plotting.image.plotImage(evt["analysis"]["fit"], msg=msg_fit, log=True, mask=m)
        
        # Plot heatmap of injector pos in x vs. diameter
        plotting.correlation.plotHeatmap(evt["parameters"]["injector_posx"], evt["analysis"]["diameter"], **heatmapInjector)

        # Plot heatmap of center positions
        plotting.correlation.plotHeatmap(evt["analysis"]["offCenterX"], evt["analysis"]["offCenterY"], **heatmapCenterPos)


        
