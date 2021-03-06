"""
Simulator for Ptychography experiment at LCLS

Some details for AMO:
=====================
dector: distance 731 mm, size (1024x1024)/4 => 512x512
        pixel size 75 um
sample: finest feature .5 um, diameter 200 um
        Si3N4 thickness 1 um Vs structure height 1.6 um +- .016 (i.e. only gold on substrate ??)
energy: ca. .85 keV => (6.6*.3)/(.8*1.6) nm .. ca. 1.5 nm

authors: Simone Sala, Benedikt J. Daurer (benedikt@xray.bmc.uu.se)
"""
import scipy.ndimage as ndi
import PIL.Image as Image
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import h5py
import sys

class Simulation:
    def __init__(self, nperpos=10, scanx=4, scany=4, scanstep=50, wavelength=1e-10, frame_width=512):
        """
        Simulator for Ptychography experimetns at LCLS.
        
        Kwargs:
            :nperpos(int): Nr. of shots per scanning position, default=50
            :scanx(int): Nr. of horizontal scanning positions, default=10
            :scany(int): Nr. of vertical scanning positions, default=10
            :scanstep(int): Step size of scanning procedure in [px], default=20
            :wavelength(float): Photon wavelength given in [m], default=1e-10
            :frame_width(int): Sidelength of detector in [px], default=512

        :Authors:
            Simone Sala,
            Benedikt J. Daurer (benedikt@xray.bmc.uu.se)
        """
        self.nperpos     = nperpos
        self.scanx       = scanx
        self.scany       = scany
        self.nframes     = nperpos * scanx * scany
        self.scanstep    = scanstep
        self.frame_width = frame_width
        self.wavelength  = wavelength
        self.counter = 0

    def crop(self, img):
        """
        Cropping images of sidelength self.image_side to a side_length of self.frame_width
        """
        ofs = (self.image_side-self.frame_width)//2
        return img[ofs:-ofs,ofs:-ofs]
        
    def getMode(self, rampxy=[0,0]):
        """
        Returns the probe with a phase ramp applied. The phase ramp is defined by shifting the probe in fourier space.

        Kwargs:
            :rampxy: A list with shifts [x,y], default = [0,0]
        """
        return np.fft.ifftn(np.roll(np.roll( np.fft.fftn(self.illumination), rampxy[0], axis=0),rampxy[1], axis=1))
                                                                            
    def getRandomMode(self, sramp=5.):
        """
        Returns the probe with a randomized phase ramp applied. The phase ramp is defined by shifting the probe in fourier space.

        Kwargs:
            :sramp: Standard deviation of normal distributation, a random shift is picked based on that distribution, default=5.
        """
        rxy = np.round(np.random.normal(size=(2,), scale=sramp)).astype(int)
        return self.getMode(rxy)
        
    def loadBinarySample(self, filename, smooth=2.):
        """
        Loads a binary sample from a given file, assuming squared images.

        Args:
            :filename(str): Sample file to be loaded (.png) 
            :smooth(int):   Std of gaussian filter applied to the image
        """
        with Image.open(filename) as f:
            nr_channels = len(f.mode)
            nx, ny = f.size            
            assert nx == ny, "Can only load square images"
            self.image_side = nx
            sample = np.array(f.getdata()).reshape((self.image_side,self.image_side,nr_channels))
            self.sample = 1-sample[:,:,0]/255.
            self.sample = ndi.gaussian_filter(self.sample, 2.)
        print "Done loading binary sample from file: ", filename

    def loadSiemensStar(self, size):
        """
        Loads modelled Siemens star patterns (from ptypy.utils)

        """
        try:
            import ptypy
        except ImportError:
            print "Siemens star cannot be loaded with the ptypy package (https://github.com/ptycho/ptypy)"
        self.image_side = size
        self.sample = ptypy.utils.xradia_star((self.image_side, self.image_side),spokes=60,minfeature=1,ringfact=1.8,rings=5)
        #ADD 'cut' spoke .. refine model !!
        
        
    def defineIllumination(self, shape='gaussian', object_radius=15e-6, illumination_radius=500e-9):
        """
        Defines a 'flat' or 'gaussian' illumination.

        Kwargs:
            :shape(str): flat or gaussian (default)
            :object_radius(float): Radius of the object in [m], default = 15e-6
            :illumination_radius(float): Radius of the illumination in [m], default = 500e-9
        """
        x = np.arange(-self.image_side/2, self.image_side/2, 1).astype(float)
        y = np.arange(-self.image_side/2, self.image_side/2, 1).astype(float)
        xv, yv = np.meshgrid(x, y)
        r = np.sqrt(xv**2 + yv**2)
        pixel_size = object_radius / self.image_side #object_radius assumed to cover all FOV

        if shape == 'flat':
            self.illumination = np.array(r<(illumination_radius/pixel_size))
        elif shape == 'gaussian':
            self.illumination = np.exp(-.5*(r*pixel_size)**2/illumination_radius**2)
        else:
            print "Shape of illumination has to be of type 'flat' or 'gaussian'"

    def defineExitWave(self, sample_thickness=200e-9, offCenterX=100, offCenterY=100):
        """
        Creates probe and object of sample given some values for transmission.

        Kwargs:
            :sample_thickness: Thickness of sample in [m], default=200e-9
            :offCenterX: horizontal centershift of the FOV in [px], default = 100
            :offCenterY: vertical centershift of the FOV in [px], default = 100
        """
        # Rough transmission parameters (hard-coded), complex
        tr = 2*np.pi*(2.26952016E-05 - 1.42158774E-06j)*sample_thickness/self.wavelength

        # Define object
        self.obj = np.exp(-1j*tr*self.sample)
        
        # Define probe (with phase ramp)
        self.probe = self.crop(self.getMode([3,2]))
        
        # Crop the object (and move off-center) .. asymmetrically
        #self.obj = self.obj[self.image_side - self.frame_width - offCenterY:self.image_side - offCenterY,
        #                    self.image_side - self.frame_width - offCenterX:self.image_side - offCenterX]

        # Exit wave
        #self.exitwave = self.probe * self.obj
        #THIS IS NOT USED !!

    def getPositions(self):
        """
        Returns scanning positions
        """
        offset = 0
        positions = np.zeros((self.scanx*self.scany,2))
        counter = 0
        for i in range(self.scanx):
            for j in range(self.scany):
                positions[counter] = [offset + self.scanstep*i,offset + self.scanstep*j]
                counter += 1
        self.positions = positions
    
    def scanSample(self, i):
        """
        Returns the object at given position index.
        """
        
        obj_size_x = np.shape(self.obj)[1]
        obj_size_y = np.shape(self.obj)[0]
        A_size_x = self.frame_width + ((self.scanx-1)*self.scanstep)
        A_size_y = self.frame_width + ((self.scany-1)*self.scanstep)
        A = np.ones((A_size_x,A_size_y)).astype(np.complex)
        A[
((A_size_y > obj_size_y)*( A_size_y - obj_size_y)/2):
((A_size_y > obj_size_y)*(-A_size_y + obj_size_y)/2)+A_size_y,((A_size_x > obj_size_x)*( A_size_x - obj_size_x)/2):
((A_size_x > obj_size_x)*(-A_size_x + obj_size_x)/2)+A_size_x
] = self.obj[
((A_size_y < obj_size_y)*(-A_size_y + obj_size_y)/2):
((A_size_y < obj_size_y)*( A_size_y - obj_size_y)/2)+obj_size_y,
((A_size_x < obj_size_x)*(-A_size_x + obj_size_x)/2):
((A_size_x < obj_size_x)*( A_size_x - obj_size_x)/2)+obj_size_x
]
        return A[self.positions[i,0]:self.positions[i,0]+self.frame_width,
                 self.positions[i,1]:self.positions[i,1]+self.frame_width]


    def propagate(self):
        """
        Creates a set of diffraction patterns.
        """
        self.getPositions()
        frames = []
        self.scan_objs = np.zeros((np.shape(self.positions)[0],self.frame_width,self.frame_width)).astype(np.complex)
        for j in range(self.positions.shape[0]):
            self.scan_obj = self.scanSample(j)
            self.scan_objs[j] = self.scan_obj
            for i in range(self.nperpos):
                self.scan_illumination = self.crop(self.getRandomMode(5.))
                f = np.fft.fftshift(abs(np.fft.fftn(self.scan_illumination*self.scan_obj))**2)
                Itot = 10e7 * np.random.normal()**2 # Not sure if that is good, think about proper simulation using an estimated of photon flux
                frames.append(np.random.poisson(Itot*f/f.sum()))
        self.frames = np.array(frames)

    def get_next_frame(self):
        frame = self.frames[self.counter % self.nframes]
        self.counter += 1
        return frame

    def get_sample_image(self):
        #return np.abs(self.scan_obj)
        return np.abs(self.scan_objs[(self.counter / self.nperpos) % (self.nframes / self.nperpos)])

    def get_illumination(self):
        return np.abs(self.scan_illumination)

    def get_position_x(self):
        return self.positions[(self.counter / self.nperpos) % (self.nframes / self.nperpos),0]

    def get_position_y(self):
        return self.positions[(self.counter / self.nperpos) % (self.nframes / self.nperpos),1]

    def get_position_n(self):
        return (self.counter % self.nframes) // (self.positions.shape[0])

if __name__ == '__main__':

    # Define the experiment
    sample_filename = 'pseudo_star.png'

    # Simulate the experiment
    sim = Simulation()
    sim.loadBinarySample(sample_filename)
    sim.defineIllumination()
    sim.defineExitWave()
    sim.propagate()
    
    # Save frames to file
    #np.save('frames_%s.npy' %N, sim.frames)

    # Some plotting
    fig = plt.figure()
    ax1 = fig.add_subplot(121)
    ax1.imshow(np.angle(sim.obj), cmap='gray', interpolation='nearest')
    ax1.set_title('Sample')
    ax2 = fig.add_subplot(122)
    ax2.imshow(sim.frames.mean(axis=0) + 1e-8, norm=LogNorm(vmin=1), cmap='gnuplot', interpolation='nearest')
    ax2.set_title('Simulated diffraction')
    plt.show()
    
               
    
    

