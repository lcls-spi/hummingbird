import time
import analysis.event
import analysis.beamline
import analysis.background
import analysis.pixel_detector
import ipc
import numpy
from backend import ureg

state = {
    'Facility': 'Dummy',

    'Dummy': {
        # The event repetition rate of the facility 
        'Repetition Rate' : 1,
        # Dictionary of data sources
        'Data Sources': {
            # The name of the data source. This is the key under which it will be found
            # when iterating over members of its type.
            # It's also the native key that will be used
            'CCD': {
                # A function that will generate the data for every event
                'data': lambda: numpy.random.rand(256,128),
                # The units to be used
                'unit': ureg.ADU,     
                # The name of the category for this data source.
                # All data sources are aggregated by type, which is the key
                # used when asking for them in the analysis code.
                'type': 'photonPixelDetectors'
            }
        }        
    }
}

def onEvent(evt):
    ipc.broadcast.init_data('CCD', xmin=10,ymin=10)
    analysis.pixel_detector.plotImages(evt['photonPixelDetectors'])
    analysis.event.printProcessingRate(evt)
