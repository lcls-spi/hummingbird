import time
import analysis.event
import analysis.stack
import analysis.pixel_detector
import analysis.hitfinding
import plotting.image
import plotting.line
import utils.reader
import os,sys
this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(this_dir)

from backend import add_record

# Common mode correction along fastest changing dimension
do_cmc = True

# ---------------------------------------------------------
# P S A N A
# ---------------------------------------------------------
state = {}
state['Facility'] = 'LCLS'
#state['LCLS/DataSource'] = 'exp=amo86615:run=3'
state['LCLS/DataSource'] = 'shmem=psana.0:stop=no'
state['LCLS/PsanaConf'] = this_dir + 'psana_cfg/pnccd.cfg'



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
    front_type = "image"
    front_key  = "pnccdFront[%s]" % front_type

    back_type = "image"
    back_key  = "pnccdBack[%s]" % back_type


    # ------------------- #
    # INITIAL DIAGNOSTICS #
    # ------------------- #

    # Time measurement
    analysis.event.printProcessingRate()

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
 


    
