import time
import analysis.event
import analysis.stack
import plotting.image
import os,sys
this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(this_dir)

# ---------------------------------------------------------
# P S A N A
# ---------------------------------------------------------
state = {}
state['Facility'] = 'LCLS'
state['LCLS/DataSource'] = 'exp=amo86615:run=3'
state['LCLS/PsanaConf'] = 'psana_cfg/pnccd.cfg'

front_type = "image"
front_key  = "pnccdFront[%s]" % front_type

back_type = "image"
back_key  = "pnccdBack[%s]" % back_type

# Backgrounds
# -----------
Nbg   = 100
rbg   = 100
obg   = 100
bg_front = analysis.stack.Stack(name="bg_front",maxLen=Nbg,outPeriod=obg,reducePeriod=rbg)
bg_back = analysis.stack.Stack(name="bg_back",maxLen=Nbg,outPeriod=obg,reducePeriod=rbg)
bg_dir = this_dir + "/stack"

# ---------------------------------------------------------
# E V E N T   C A L L
# ---------------------------------------------------------

def onEvent(evt):

    # ------------------- #
    # INITIAL DIAGNOSTICS #
    # ------------------- #

    # Time measurement
    #analysis.event.printProcessingRate()
    #analysis.event.printID(evt["eventID"])
    #print evt["photonPixelDetectors"].keys()
    #from IPython.core.debugger import Tracer
    #Tracer()()
    #print evt.keys()
    #evt["psana.PNCCD.FramesV1"]["DetInfo(Camp.0:pnCCD.0)"]
    plotting.image.plotImage(evt[front_type][front_key], 
                             msg='', name="pnCCD front", vmin=0, vmax=10000 )     
    plotting.image.plotImage(evt[back_type][back_key], 
                             msg='', name="pnCCD back", vmin=0, vmax=10000 )     
    print evt[front_type][front_key].data.shape
    print evt[back_type][back_key].data.shape

    # COLLECTING BACKGROUND
    # Update
    bg_front.add(evt[front_type][front_key].data)
    bg_back.add(evt[back_type][back_key].data)
    # Reduce
    bg_front.reduce()
    bg_back.reduce()
    # Write to file
    bg_front.write(evt,directory=bg_dir)
    bg_back.write(evt,directory=bg_dir)
