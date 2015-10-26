
#%%

"""
dector: distance 731 mm, size (1024x1024)/4 => 512x512
        pixel size 75 um
sample: finest feature .5 um, diameter 200 um
        Si3N4 thickness 1 um Vs structure height 1.6 um +- .016 (i.e. only gold on substrate ??)
energy: ca. 500 eV => (6.6*300)/(500*1.6) nm .. ca. 2.5 nm
"""




### from simulations/LCLS_simul/test_ramp_only.py

import sys
sys.path.append('/Users/simone/Documents/Simone/Squola/2014-2015 (PhD)/simulations/LCLS_simul') #to import mode_recovery from folder

import scipy.ndimage     as ndi
import PIL.Image         as Image
import matplotlib.pyplot as plt
import numpy             as np
import pyE17.utils       as U
import h5py
import ptypy
import mode_recovery


class Experiment:
    def __init__(self, N, wavelength):
        self.N = N
        self.lam = wavelength
        self.image_side = 1024
        # The assumed illumination radius is 500nm
        self.illumination_radius = 500e-9;
        # the radius of the star is 15 um
        self.siemens_radius = 15e-6;
        self.pixel_size = self.siemens_radius / self.image_side #so siemens_radius assumed to cover all FOV
        
        x = np.arange(-self.image_side/2, self.image_side/2, 1).astype(float)
        y = np.arange(-self.image_side/2, self.image_side/2, 1).astype(float)
        xv, yv = np.meshgrid(x, y)
        r = np.sqrt(xv**2 + yv**2)

        # Disk as the illumination shape
        #self.illumination = np.array(r<(illumination_radius/pixel_size))
        # ... or Gaussian
        self.illumination = np.exp(-.5*(r*self.pixel_size)**2/self.illumination_radius**2)
    
    
    
    def create_mode(self, rampxy):
        """
        Only ramp
        """
        return np.fft.ifftn( np.roll(
                             np.roll( np.fft.fftn(self.illumination), rampxy[0], axis=0),
rampxy[1], axis=1) )
                                                                            
    def random_mode(self, sramp):
        rxy = np.round(np.random.normal(size=(2,), scale=sramp)).astype(int)
        return self.create_mode(rxy)
    
    def get_modes(self):
        # Generate modes
        sr = 3.
        n_r = np.ceil(3*sr).astype(int)
        rj = np.mgrid[-n_r:n_r,-n_r:n_r]
        rjf = rj.reshape((2,-1))
        prob = np.exp(-((rjf/sr)**2).sum(axis=0)) / (sr**2 * np.pi)
        
        self.N1 = 512
        tol = 1e-2
        
        ofs = (self.image_side-self.N1)//2
        thres = prob.max() * tol
        #print sum(prob>thres)
        t = [self.create_mode(rjf[:,i])[ofs:-ofs,ofs:-ofs] for i in range(rjf.shape[-1]) if prob[i] > thres] 
        
        # Get modes
        return ptypy.utils.ortho(t)
    
    def prep_Siemens(self):
        # Load sample
        siemens = np.array(Image.open('/Users/simone/Documents/Simone/Squola/2014-2015 (PhD)/simulations/LCLS_simul/Siemens_star.png').getdata()).reshape((self.image_side,self.image_side,4))
        siemens = 1-siemens[:,:,0]/255.
        print 'done loading Siemens star'
        
        # Rough transmission parameters
        tr = 2*np.pi*(2.26952016E-05 - 1.42158774E-06j)*200e-9/1e-10
        obj = np.exp(-1j*tr*siemens)
        
        # Generate a new shot and try to recover the modes
        r = np.array([3,2])
        ofs = (self.image_side-self.N1)//2
        probe = self.create_mode(r)[ofs:-ofs,ofs:-ofs]
        obj1 = obj[400:400+self.N1,400:400+self.N1]
        
        return probe, obj1, obj
    
    
    def shift_Siemens(self, probe, obj, doplot=False, dosave=False):
        #######################################################
        #######################################################
        
        #positions = np.array([[400-1,700-1]]) #within 0:last of siesta; it represents the upper left point of the 4x4 centre (assuming even arrays)
        raster_size_x = 11 #number of elements, i.e. intervals + 1
        raster_size_y = 11 #number of elements, i.e. intervals + 1
        raster_0      = 0
        raster_step   = 100
        positions = np.zeros((raster_size_x*raster_size_y,2))
        counter = 0
        for i in range(raster_size_x):
            for j in range(raster_size_y):
                positions[counter] = [raster_0 + raster_step*i,raster_0 + raster_step*j]
                counter += 1
        #positions = np.array([[200,300]])
        
        for i in range(np.shape(positions)[0]):
         
            sample  = np.ones((np.shape(probe)[0],np.shape(probe)[1]))
            
            j0_min = 0
            j0_max = np.shape(sample)[0]
            j1_min = 0
            j1_max = np.shape(sample)[0]
            i0_min = positions[i,0] - np.shape(sample)[0]/2 + 1
            if  i0_min < 0:
                j0_min-= i0_min
                i0_min = 0
            i0_max = positions[i,0] + np.shape(sample)[0]/2 + 1
            if  i0_max > np.shape(obj)[0]:
                j0_max = np.shape(obj)[0] - i0_max
                i0_max = np.shape(obj)[0]
            i1_min = positions[i,1] - np.shape(sample)[0]/2 + 1
            if  i1_min < 0:
                j1_min-= i1_min
                i1_min = 0
            i1_max = positions[i,1] + np.shape(sample)[0]/2 + 1
            if  i1_max > np.shape(obj)[1]:
                j1_max = np.shape(obj)[1] - i1_max
                i1_max = np.shape(obj)[1]
            #print (i0_min,i0_max,i1_min,i1_max,j0_min,j0_max,j1_min,j1_max)
            
            sample[j0_min:j0_max,j1_min:j1_max] = obj[i0_min:i0_max,i1_min:i1_max]
            
            shot = probe * sample  
            I0 = np.fft.fftshift(abs(np.fft.fftn(shot))**2)
            if doplot:
                plt.figure()
                plt.subplot(1,2,1)
                plt.imshow(np.log(abs(I0)))
                dontprint = plt.axis('off') #dontprint is just not to show a printed line on terminal for every subplot
                plt.subplot(1,2,2)
                plt.imshow(abs(sample))
                dontprint = plt.axis('off') #same as above
                if dosave: plt.savefig('/Users/simone/Documents/Simone/Squola/2014-2015 (PhD)/simulations/img/Siemens_%s.png' %str(1000+i))
                plt.close()
        
        #######################################################
        #######################################################
        return 1.
    
    def multiplot(self,tot,to_be_plotted,interval=1,from_first=True):
        #tot is the size of the side of the square subplot (e.g. tot = 3 => subplot 3x3)
        #to_be_plotted is the 3D array from which 2D arrays are taken for the subplot
        #interval is the step_size for the for-loop (e.g. take every other frame would be interval = 2, etc.)
        counter = 0
        plt.figure()
        for i in range(tot**2):
            plt.subplot(tot,tot,counter+1)
            if from_first:
                index = counter*interval
            else:
                index = -1-(counter*interval)
            plt.imshow(abs(to_be_plotted[index]))
            plt.axis('off')
            counter += 1
        return 1.
    
    def actually_do_stuff(self):
        
        
        a,m = self.get_modes()
        probe, obj1, obj = self.prep_Siemens()
        
        shot = probe * obj1
        
        I0 = np.fft.fftshift(abs(np.fft.fftn(shot))**2)
        
        pcount = 1e6
        Is = I0.sum()
        I = Is * np.random.poisson(I0*pcount/Is) / pcount
        
        cutoff = 8
        mo = [mm * obj1 for mm in m[:cutoff]]
        ao1, mo1 = ptypy.utils.ortho(mo)
        fm = []
        for mm in mo1:
            fm1 = np.fft.fftshift(np.fft.fftn(mm))
            fm1 /= np.sqrt((abs(fm1)**2).sum())
            fm.append(fm1)
        fm = np.array(fm)
        
        # Try with the solution
        fshot = np.fft.fftshift(np.fft.fftn(shot))
        csol = np.tensordot(fshot, fm.conj(), axes=((0,1),(1,2)))
        
        
        c, err = mode_recovery.recompose_DM(I,fm)
        
        cn = c/c[0]
        csoln = csol/csol[0]
        
        ofs = (self.image_side-self.N1)//2
        
        obj1a = ndi.gaussian_filter(obj1.real, 2.) + 1j * ndi.gaussian_filter(obj1.imag, 2.)
        frames = []
        for i in range(self.N):
            #f = np.fft.fftshift(abs(np.fft.fftn(self.random_mode(5., 5.)[ofs:-ofs,ofs:-ofs]*obj1a))**2)
            f = np.fft.fftshift(abs(np.fft.fftn(self.random_mode(5.)[ofs:-ofs,ofs:-ofs]*obj1a))**2)
            Itot = 10e7 * np.random.normal()**2
            frames.append(np.random.poisson(Itot*f/f.sum()))
        
        
        frames = np.array(frames)
        """
        plt.figure()
        fmean = frames.mean(axis=0)
        U.franzmap()
        
        plt.imshow(np.log(fmean+1)); plt.draw()
        plt.colorbar()
        
        self.multiplot(3,m,from_first=False)
        """
        
        return frames
    

### USE np.save(file,arr) e np.load(file)


if __name__ == '__main__':
    N = 50
    wavelength = 1e-10
    exp = Experiment(N,wavelength)
    frames = exp.actually_do_stuff()
    np.save('frames_%s.npy' %N, frames)
    print 'saved frames'

#%%
