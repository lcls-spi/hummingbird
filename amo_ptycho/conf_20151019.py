import time
import analysis.event
import analysis.beamline
import analysis.pixel_detector
import analysis.stats
import plotting.image
import ipc
import numpy
import numpy.random
from backend import add_record

N = 50
frames = numpy.load('frames_%s.npy' %N)
## or run 'experiment' directly
frames[frames<=0.] =1.

numpy.random.seed()

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
                'data': lambda: numpy.log(frames[numpy.random.randint(0,N)]),
                # The units to be used
                'unit': 'ADU',     
                # The name of the category for this data source.
                # All data sources are aggregated by type, which is the key
                # used when asking for them in the analysis code.
                'type': 'photonPixelDetectors'
            }
        }        
    }
}

data_stats = analysis.stats.DataStatistics()

def onEvent(evt):
    ipc.broadcast.init_data('CCD')#, xmin=10,ymin=10)
    for k,v in evt['photonPixelDetectors'].iteritems():
        plotting.image.plotImage(v)

    data_stats.add(evt['photonPixelDetectors'].values()[0].data)
    mean = add_record(evt["analysis"], "analysis", "pnCCD front (mean)", data_stats.min(), unit='')
    plotting.image.plotImage(evt["analysis"]["pnCCD front (mean)"], 
                             msg='', name="pnCCD front (mean)")
    #if (not ipc.mpi.is_main_slave())
    analysis.event.printProcessingRate()
