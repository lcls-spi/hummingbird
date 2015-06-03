import os
import time
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

# Model parameters for sphere
# ---------------------------
modelParams = {
    'wavelength':0.1907,
    'pixelsize':110,
    'distance':2400,
    'adu_per_photon':26,
    'quantum_efficiency':1.,
    'material':'virus'}

# Sizing parameters
# -----------------
sizingParams = {
    'd0':100,
    'i0':1,
    'mask_radius':300,
    'downsampling':1,
    'brute_evals':40,
    'photon_counting':True}

this_dir = os.path.dirname(os.path.realpath(__file__))
greader = utils.reader.GeometryReader(this_dir + "/geometry.h5")
mreader = utils.reader.MaskReader(this_dir + "/mask.h5","/data/data")
mask    = utils.array.assembleImage(greader.x, greader.y, mreader.boolean_mask, nx=414, ny=414, dtype='bool')

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
    if evt["analysis"]["isHit - CCD"]:

        print "It's a hit"

        t0 = time.time()
        # Find the center of diffraction
        analysis.sizing.findCenter(evt, "photonPixelDetectors", "CCD", mask=mask, maxshift=40, threshold=13, blur=4)
        t_center = time.time()-t0
        
        # Fitting sphere model to get size and intensity
        t0 = time.time()
        analysis.sizing.fitSphere(evt, "photonPixelDetectors", "CCD", mask=mask, **dict(modelParams, **sizingParams))
        t_size = time.time()-t0

        # Fitting model
        t0 = time.time()
        analysis.sizing.sphereModel(evt, "analysis", "offCenterX", "offCenterY", "diameter", "intensity", (sim.ny,sim.nx), poisson=True, **modelParams)
        t_full = time.time()-t0

        t_all = t_center + t_size + t_full
        print "Time: %e sec (center / size / full : %.2f%% / %.2f%% / %.2f%%)" % (t_all, 100.*t_center/t_all, 100.*t_size/t_all, 100.*t_full/t_all)
        
        plotting.line.plotHistory(evt["analysis"]["offCenterX"])
        plotting.line.plotHistory(evt["analysis"]["offCenterY"])
        plotting.line.plotHistory(evt["analysis"]["diameter"])
        plotting.line.plotHistory(evt["analysis"]["intensity"])
        plotting.line.plotHistory(evt["analysis"]["error"])

        # Attach a message to the plots
        s0 = evt["analysis"]["diameter"].data
        I0 = evt["analysis"]["intensity"].data
        msg_glo = "diameter = %.2f nm, \nintensity = %.2f mJ/um2" % (s0, I0)
        msg_fit = "Fit result: \ndiameter = %.2f nm, \nintensity = %.2f mJ/um2" % (s0, I0)

        # Plot the glorious shots
        plotting.image.plotImage(evt["photonPixelDetectors"]["CCD"], msg=msg_glo, log=True, mask=mask)
        
        # Plot the fitted model
        plotting.image.plotImage(evt["analysis"]["fit"], msg=msg_fit, log=True, mask=mask)

        # Bin image
        analysis.pixel_detector.bin(evt, "photonPixelDetectors", "CCD")

        # Plot binned image
        plotting.image.plotImage(evt["analysis"]["CCD - binned"], log=True)
                
        # Plot heatmap of injector pos in x vs. diameter
        plotting.correlation.plotHeatmap(evt["parameters"]["injector_posx"], evt["analysis"]["diameter"], **heatmapInjector)

        # Plot heatmap of center positions
        plotting.correlation.plotHeatmap(evt["analysis"]["offCenterX"], evt["analysis"]["offCenterY"], **heatmapCenterPos)
