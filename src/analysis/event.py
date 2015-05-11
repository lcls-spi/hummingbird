import collections
import datetime
import ipc
import numpy

def printKeys(evt):
    print evt.keys()    

def printNativeKeys(evt):
    print evt.native_keys()

def printID(eventID):
    for k,v in eventID.iteritems():
        print "%s = %s" %(k, v.data)
        try:
            print "datetime64 = %s" %(v.datetime64)
        except AttributeError:
            pass
        try:
            print "fiducials = %s" %(v.fiducials)
        except AttributeError:
            pass
        try:
            print "run = %s" %(v.run)
        except AttributeError:
            pass
        try:
            print "ticks = %s" %(v.ticks)
        except AttributeError:
            pass
        try:
            print "vector = %s" %(v.vector)
        except AttributeError:
            pass

eventFiducialDeque = collections.deque([],100)
def plotFiducial(eventID):
    for k,v in eventID.iteritems():
        eventFiducialDeque.append(v.fiducials)
        #ipc.set_data("Event Fiducials", eventFiducialDeque)
        ipc.new_data(k, v.fiducials)

processingTimes = collections.deque([], 100)
def printProcessingRate(evt = None):
    processingTimes.appendleft(datetime.datetime.now())
    if(len(processingTimes) < 2):
        return
    dt = processingTimes[0] - processingTimes[-1]
    proc_rate = numpy.array((len(processingTimes)-1)/dt.total_seconds())
    
    ipc.mpi.sum(proc_rate)
    if(ipc.mpi.is_main_worker()):
        ipc.new_data('Processing Rate', proc_rate[()])



    
