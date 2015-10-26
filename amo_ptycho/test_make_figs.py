from PIL import Image
import numpy as np
import h5py
import ptypy

image_side = 1024
# The assumed illumination radius is 500nm
illumination_radius = 500e-9;
# the radius of the star is 15 um
siemens_radius = 15e-6;
pixel_size = siemens_radius / image_side

x = np.arange(-image_side/2, image_side/2, 1).astype(float)
y = np.arange(-image_side/2, image_side/2, 1).astype(float)
xv, yv = np.meshgrid(x, y)
r = np.sqrt(xv**2 + yv**2)

# Disk as the illumination shape
#illumination = np.array(r<(illumination_radius/pixel_size))
# ... or Gaussian
illumination = np.exp(-.5*(r*pixel_size)**2/illumination_radius**2)
def create_mode(rampxy, jitterxy):
    return np.roll(
           np.roll( np.fft.ifftn( np.roll(
                                  np.roll( np.fft.fftn(illumination), rampxy[0], axis=0),
                                                                      rampxy[1], axis=1) ), jitterxy[0], axis=0),
                                                                                            jitterxy[1], axis=1)
def random_mode(sramp, sjitter):
    rxy = np.round(np.random.normal(size=(2,), scale=sramp)).astype(int)
    jxy = np.round(np.random.normal(size=(2,), scale=sjitter)).astype(int)
    return create_mode(rxy, jxy)

N1 = 512
ofs = (image_side-N1)//2

# Load sample
siemens = np.array(Image.open('Siemens_star.png').getdata()).reshape((image_side,image_side,4))
siemens = 1-siemens[:,:,0]/255.

# Rough transmission parameters
tr = 2*np.pi*(2.26952016E-05 - 1.42158774E-06j)*200e-9/1e-10
obj = np.exp(-1j*tr*siemens)

obj1 = obj[400:400+N1,400:400+N1]

obj1a = ndi.gaussian_filter(obj1.real, 2.) + 1j * ndi.gaussian_filter(obj1.imag, 2.)
frames = []
for i in range(50):
    f = np.fft.fftshift(abs(np.fft.fftn(random_mode(5., 5.)[ofs:-ofs,ofs:-ofs]*obj1a))**2)
    Itot = 10e7 * np.random.normal()**2
    frames.append(np.random.poisson(Itot*f/f.sum()))

frames = np.array(frames)
fmean = frames.mean(axis=0)

from pyE17 import utils as U
from matplotlib import cm
lfmax = np.log(frames.max())
for i, f in enumerate(frames):
    U.imsave(log(f[128:-128, 128:-128]+1), 'imgs/single_shot_simulation_%02d.png' % i, vmin=0, vmax=lfmax, cmap=cm.get_cmap('franzmap'))
U.imsave(log(fmean[128:-128, 128:-128]+1), 'imgs/single_shot_simulation_avg.png', vmin=0, vmax=lfmax, cmap=cm.get_cmap('franzmap'))
for i in range(4):
    U.imsave(random_mode(5., 5.)[256:-256, 256:-256], 'imgs/random_mode_%02d.png' % i)
