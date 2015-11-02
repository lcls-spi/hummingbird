import time
import analysis.event
import analysis.beamline
import analysis.pixel_detector
import analysis.stats
import plotting.image
import plotting.line
import ipc
import numpy
import numpy.random
from backend import add_record
from simulation.ptycho import Simulation

# Define the experiment
sample_filename = 'amo_ptycho/pseudo_star.png'

# Simulate the experiment
print "Simulating the ptychography experiment, this might take a few seconds..."
sim = Simulation()
#sim.loadBinarySample(sample_filename)
sim.loadSiemensStar(1024)
sim.defineIllumination()
sim.defineExitWave()
sim.propagate()

state = {
    'Facility': 'Dummy',

    'Dummy': {
        # The event repetition rate of the facility 
        'Repetition Rate' : 5,
        # Dictionary of data sources
        'Data Sources': {
            # The name of the data source. This is the key under which it will be found
            # when iterating over members of its type.
            # It's also the native key that will be used
            'CCD': {
                # A function that will generate the data for every event
                #'data': lambda: numpy.log(frames[numpy.random.randint(0,N)]),
                'data': lambda: sim.get_next_frame(),
                # The units to be used
                'unit': 'ADU',     
                # The name of the category for this data source.
                # All data sources are aggregated by type, which is the key
                # used when asking for them in the analysis code.
                'type': 'photonPixelDetectors'
            },
            'sample': {
                'data': lambda: sim.get_sample_image(),
                'unit': '',
                'type': 'simulation'
                },
            'illumination': {
                'data': lambda: sim.get_illumination(),
                'unit': '',
                'type': 'simulation'
                },
            'position_x': {
                'data': lambda: sim.get_position_x(),
                'unit': 'm',
                'type': 'simulation'
                },
            'position_y': {
                'data': lambda: sim.get_position_y(),
                'unit': 'm',
                'type': 'simulation'
                },
            'position_n': {
                'data': lambda: sim.get_position_n(),
                'unit': '',
                'type': 'simulation'
            }
        }        
    }
}

data_stats = analysis.stats.DataStatistics()

def onEvent(evt):

    # Plotting
    # ========

    # 1. Sample image (at current scan position)
    plotting.image.plotImage(evt['simulation']['sample'], name='Siemens star',
                             msg='posx = %d, posy = %d' %(evt['simulation']['position_x'].data, (evt['simulation']['position_y'].data)))

    # 2. Illumination (at current scan position)
    plotting.image.plotImage(evt['simulation']['illumination'], name='Illumination',
                             msg='posn = %d' %(evt['simulation']['position_n'].data))

    # 2. CCD
    plotting.image.plotImage(evt['photonPixelDetectors']["CCD"],
                             msg='CCD', name='CCD', log=True)

    # 3. Scanning positions
    plotting.line.plotHistory(evt['simulation']['position_x'])
    plotting.line.plotHistory(evt['simulation']['position_y'])
    plotting.line.plotHistory(evt['simulation']['position_n'])
                             
    
    # Print processing rate
    analysis.event.printProcessingRate()
