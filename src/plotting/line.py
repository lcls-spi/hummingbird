"""A plotting module for line plots"""
import numpy as np
import ipc
import utils.array


histories = {}
def plotHistory(param, label='', history=100, runningHistogram=False, window=20, bins=100, hmin=0, hmax=100, name_extension=""):
    """Plotting history of a parameter.

    Args:
        :param(Record):  The history is based on param.data

    Kwargs:
        :label(str):     Label for param
        :history(int):   Length of history buffer
    """
    if param is None:
        return
    plotid = "History(%s)%s" % (param.name, name_extension)
    if (not param.name in histories):
        if runningHistogram:
            data_type = 'running_hist'
            ipc.broadcast.init_data(plotid, data_type=data_type, ylabel=label, history_length=history, window=window, bins=bins, hmin=hmin, hmax=hmax)
        else:
            data_type = 'scalar'
            ipc.broadcast.init_data(plotid, data_type=data_type, ylabel=label, history_length=history)
        histories[param.name] = True
    ipc.new_data(plotid, param.data)

def plotTimestamp(timestamp):
    ipc.new_data('History(Fiducial)', timestamp.fiducials)

histograms = {}
def plotHistogram(param, hmin=None, hmax=None, bins=100, label='', density=False, history=100, mask=None, log10=False, name_extension=""):
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
    plotid = "Histogram(%s)%s" % (param.name, name_extension)
    if(not param.name in histograms):
        ipc.broadcast.init_data(plotid, data_type='vector', xlabel=label, history_length=history)
        histograms[param.name] = True
    data = param.data
    if mask is not None:
        data = data[mask]
    if log10:
        data=np.log10(data)
    if hmin is None: hmin = data.min()
    if hmax is None: hmax = data.max()
    H,B = np.histogram(data.flat, range=(hmin, hmax), bins=bins, density=density)
    ipc.new_data(plotid, H, xmin=B.min(), xmax=B.max())

traces = {}
def plotTrace(paramY, paramX=None, label='', history=100, tracelen=None):
    """Plotting a trace.
    
    Args:
        :paramY(Record):   The data for the ordinate is paramY.data.ravel()

    Kwargs:
        :paramX(Record):   The data for the abscissa is paramX.data.ravel() if paramX is not None
        :label(str):    Label for param
        :history(int):  Length of history buffer
    """
    if paramY is None:
        return
    plotid = "Trace(%s)" %paramY.name
    if(not paramY.name in traces):
        ipc.broadcast.init_data(plotid, data_type='vector', xlabel=label, history_length=history)
        histograms[paramY.name] = True
    if paramX is None:
        ipc.new_data(plotid, data_y=paramY.data.ravel())
    else:
        x = paramX.data.ravel()
        y = paramY.data.ravel()
        if tracelen is not None:
            x = x[:tracelen]
            y = y[:tracelen]
        if x.size != y.size:
            logging.warning("For %s x- and y-dimension do not match (%i, %i). Cannot plot trace." % (plotid,x.size,y.size))
            return
        ipc.new_data(plotid, data_y=np.array([x,y], copy=False)) 

