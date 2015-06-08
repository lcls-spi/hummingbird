import os
import numpy
import analysis.event
import analysis.beamline
import analysis.hitfinding
import analysis.pixel_detector
import analysis.background
import analysis.pixel_detector
import ipc   
import utils.reader
this_dir = os.path.dirname(os.path.realpath(__file__))

state = {
    'Facility': 'LCLS',
    #'LCLS/DataSource': ipc.mpi.get_source(['/data/rawdata/LCLS/cxi/cxic9714/xtc/e419-r0203-s01-c00.xtc', 
    #                                       '/data/rawdata/LCLS/cxi/cxic9714/xtc/e419-r0204-s01-c00.xtc'])
    #'LCLS/DataSource': 'exp=cxi86715:run=10',
    'LCLS/DataSource': 'exp=cxi86415:run=1:xtc',
    #'LCLS/PsanaConf': 'psana_cfg/Ds2.cfg',
    'LCLS/PsanaConf': 'psana_cfg/Dg2.cfg',
}

# Psana identifiers
backdet_id = "CsPad Dg3[calibrated]"

##############
# PARAMETERS #
##############

# Hit finding
# -----------
aduThreshold = 10
hitscoreThreshold = 200

# Sizing
# ------
modelParams = {
    'wavelength':0.12398,
    'pixelsize':110,
    'distance':2160,
    'material':'virus',
}
sizingParams = {
    'd0':100,
    'i0':1,
    'brute_evals':10,
}

# Geometry
G_back = utils.reader.GeometryReader(this_dir + "/geometry/geometry_back.h5")

# Mask
# ----
#M_back    = utils.reader.MaskReader(this_dir + "/mask/mask_back.h5","/data/data")
#mask_back = M_back.boolean_mask


# Background
# ----------
Nbg = 100
#Nbg = 10000
bg = analysis.background.Stack(name="bg",maxLen=Nbg)

def onEvent(evt):
    #print evt["parameters"].keys()
    #analysis.beamline.printPulseEnergy(evt['pulseEnergies'])
    #analysis.beamline.printPhotonEnergy(evt['photonEnergies'])
    #print "EPICS photon energy = %g eV" %(evt['parameters']['SIOC:SYS0:ML00:AO541'].data)
    #analysis.pixel_detector.printStatistics(evt['photonPixelDetectors'])
    #analysis.pixel_detector.printStatistics(evt['ionTOFs'])
    #print "Rank = ", ipc.mpi.rank,fr analysis.event.printID(evt['eventID'])
    # Count Nr. of Photons
    #analysis.pixel_detector.totalNrPhotons(evt,"photonPixelDetectors", "CCD")

    analysis.event.printProcessingRate()
    back = evt["image"]["CsPad Dg3[image]"].data
    #analysis.pixel_detector.assemble(evt,"calibrated",backdet_id,x=G_back.x,y=G_back.y)
    #cspad2x2_ass = evt["analysis"]["assembled - "+backdet_id]
    # Update background buffer
    bg.add(back)
    # Write background to file
    bg.write(evt,directory=this_dir+"/bg",interval=100)

    # Simple hitfinding (Count Nr. of lit pixels)
    #analysis.hitfinding.countLitPixels(evt, "calibrated", backdet_id, aduThreshold=aduThreshold, hitscoreThreshold=hitscoreThreshold, mask=mask_back)

    #print evt["analysis"]["hitscore - " + backdet_id].data

    # Hit analysis
    #if evt["analysis"]["isHit - " + backdet_id]:
    #    print "HIT"
    #if evt["analysis"]["isHit - Dg2"]:
        # RADIAL SPHERE FIT
        #------------------
        # Find the center of diffraction
        #analysis.sizing.findCenter(evt, "calibrated", "Dg2", mask=mask_back, maxshift=20, threshold=0.5, blur=4)
        # Calculate radial average
        #cx = evt["analysis"]["offCenterX"].data + (nx - 1) / 2.  
        #cy = evt["analysis"]["offCenterY"].data + (ny - 1) / 2.
        #analysis.pixel_detector.radial(evt, "photonPixelDetectors", "CCD", mask=mask_back, cx=cx, cy=cy)          
        # Fitting sphere model to get size and intensity
        #analysis.sizing.fitSphereRadial(evt, "analysis", "radial distance - CCD", "radial average - CCD", **dict(modelParams, **sizingParams))
        # Calculate diffraction pattern from fit result 
        #analysis.sizing.sphereModel(evt, "analysis", "offCenterX", "offCenterY", "diameter", "intensity", (ny,nx), poisson=False, **modelParams)
        # Calculate radial average of diffraction pattern from fit result
        #analysis.pixel_detector.radial(evt, "analysis", "fit", mask=mask, cx=cx, cy=cy)
        # Output records      
        # Plot radial average
        #plotting.line.plotTrace(evt["analysis"]["radial average - CCD"], evt["analysis"]["radial distance - CCD"])
        #rlen = 100
        #ipc.new_data("radial fit", numpy.array([evt["analysis"]["radial distance - fit"].data.ravel()[:rlen], evt["analysis"]["radial average - fit"].data.ravel()[:rlen]], copy=False))
        #ipc.new_data("radial CCD", numpy.array([evt["analysis"]["radial distance - CCD"].data.ravel()[:rlen], evt["analysis"]["radial average - CCD"].data.ravel()[:rlen]], copy=False))

