import analysis.event

# ---------------------------------------------------------
# P S A N A
# ---------------------------------------------------------
state = {}
state['Facility'] = 'LCLS'
state['LCLS/DataSource'] = 'exp=amo86615:run=1'
state['LCLS/PsanaConf'] = 'psana_cfg/pnccd.cfg'

pnccd_front_type = ""

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
    print evt["pnccd-img"]
    #evt["analysis"]["pnccdFront"]
    print evt.keys()
    #plotting.image.plotImage(evt["psana.PNCCD.FramesV1"]["DetInfo(Camp.0:pnCCD.0)"], 
    #                         msg='', name="Cspad 2x2: Hit", vmin=vmin_c2x2, vmax=vmax_c2x2 )      
