import time
import analysis.event
import analysis.stack
import analysis.pixel_detector
import plotting.image
import utils.reader
import os,sys
this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(this_dir)

# Collect and write out stacks of frames
do_stacks = False
# Common mode correction along fastest changing dimension
do_cmc = True

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

# Masks
# -----
M_back    = utils.reader.MaskReader(this_dir + "/mask/mask_back.h5","/data/data")
mask_back = M_back.boolean_mask
(ny_back,nx_back) = mask_back.shape
#M_beamstops = utils.reader.MaskReader(this_dir + "/mask/beamstops_back.h5","/data/data")
#beamstops_back = M_beamstops.boolean_mask
M_front    = utils.reader.MaskReader(this_dir + "/mask/mask_front.h5","/data/data")
mask_front = M_front.boolean_mask
(ny_front,nx_front) = mask_front.shape

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

    if do_cmc:
        # CMC
        analysis.pixel_detector.cmc_pnccd(evt, back_type, back_key)
        analysis.pixel_detector.cmc_pnccd(evt, front_type, front_key)
        back_type_s = "analysis"
        back_key_s = "cmc_pnccd - " + back_key
        front_type_s = "analysis"
        front_key_s = "cmc_pnccd - " + front_key
    if not do_cmc:
        back_type_s = back_type
        back_key_s = back_key
        front_type_s = front_type
        front_key_s = front_key

    plotting.image.plotImage(evt[front_type_s][front_key_s], 
                             msg='', name="pnCCD front", vmin=0, vmax=10000, mask=mask_front)     
    plotting.image.plotImage(evt[back_type_s][back_key_s], 
                             msg='', name="pnCCD back", vmin=0, vmax=10000, mask=mask_back)     
    print evt[front_type][front_key].data.shape
    print evt[back_type][back_key].data.shape

    # COLLECTING BACKGROUND
    if do_stacks:
        # Update
        bg_front.add(evt[front_type][front_key].data)
        bg_back.add(evt[back_type][back_key].data)
        # Reduce
        bg_front.reduce()
        bg_back.reduce()
        # Write to file
        bg_front.write(evt,directory=bg_dir)
        bg_back.write(evt,directory=bg_dir)
