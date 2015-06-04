"""A plotting module for line plots"""
import numpy as np
import ipc


histories = {}
def plotHistory(param, label='', history=100):
    """Plotting history of a parameter.

    Args:
        :param(Record):  The history is based on param.data

    Kwargs:
        :label(str):     Label for param
        :history(int):   Length of history buffer
    """
    if param is None:
        return
    plotid = "History(%s)" %param.name
    if (not param.name in histories):
        ipc.broadcast.init_data(plotid, ylabel=label, history_length=history)
        histories[param.name] = True
    ipc.new_data(plotid, param.data)

histograms = {}
def plotHistogram(param, hmin=None, hmax=None, bins=100, label='', density=False, history=100):
    """Plotting a histogram.
    
    Args:
        :param(Record):   The histogram is based on param.data.flat

    Kwargs:
        :hmin(float):   Minimum, default = record.data.min()
        :hmax(float):   Maximum, default = record.data.max()
        :bins(int):     Nr. of bins, default = 100
        :label(str):    Label for param
        :density(bool): If True, the integral of the histogram is 1
        :history(int):  Length of history buffer
    """
    if param is None:
        return
    plotid = "Histogram(%s)" %param.name
    if(not param.name in histograms):
        ipc.broadcast.init_data(plotid, data_type='vector', xlabel=label, history_length=history)
        histograms[param.name] = True
    if hmin is None: hmin = param.data.min()
    if hmax is None: hmax = param.data.max()
    H,B = np.histogram(param.data.flat, range=(hmin, hmax), bins=bins, density=density)
    ipc.new_data(plotid, H, xmin=B.min(), xmax=B.max())

traces = {}
def plotTrace(paramY, paramX=None, label='', history=100):
    """Plotting a trace.
    
    Args:
        :paramY(Record):   The data for the ordinate is paramY.data.flatten()

    Kwargs:
        :paramX(Record):   The data for the abscissa is paramX.data.flatten() if paramX is not None
        :label(str):    Label for param
        :history(int):  Length of history buffer
    """
    if paramY is None:
        return
    plotid = "Histogram(%s)" %paramY.name
    if(not paramY.name in traces):
        ipc.broadcast.init_data(plotid, data_type='vector', xlabel=label, history_length=history)
        histograms[paramY.name] = True
    if paramX is None:
        ipc.new_data(plotid, data_y=paramY.data.flatten())
    else:
        ipc.new_data(plotid, data_y=paramY.data.flatten(), data_x=paramX.data.flatten())

