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

def create_mode(rampxy):
    """
    Only ramp
    """
    return np.fft.ifftn( np.roll(
                         np.roll( np.fft.fftn(illumination), rampxy[0], axis=0),
                                                             rampxy[1], axis=1) )
                                                                        
def random_mode(sramp):
    rxy = np.round(np.random.normal(size=(2,), scale=sramp)).astype(int)
    return create_mode(rxy)

# Generate modes
sr = 3.
n_r = np.ceil(3*sr).astype(int)
rj = np.mgrid[-n_r:n_r,-n_r:n_r]
rjf = rj.reshape((2,-1))
prob = np.exp(-((rjf/sr)**2).sum(axis=0)) / (sr**2 * np.pi)

N1 = 512
tol = 1e-2

ofs = (image_side-N1)//2
thres = prob.max() * tol
print sum(prob>thres)
t = [create_mode(rjf[:,i])[ofs:-ofs,ofs:-ofs] for i in range(rjf.shape[-1]) if prob[i] > thres] 

# Get modes
a,m = ptypy.utils.ortho(t)

# Load sample
siemens = np.array(Image.open('Siemens_star.png').getdata()).reshape((image_side,image_side,4))
siemens = 1-siemens[:,:,0]/255.

# Rough transmission parameters
tr = 2*np.pi*(2.26952016E-05 - 1.42158774E-06j)*200e-9/1e-10
obj = np.exp(-1j*tr*siemens)

# Generate a new shot and try to recover the modes
r = np.array([3,2])
probe = create_mode(r)[ofs:-ofs,ofs:-ofs]
obj1 = obj[400:400+N1,400:400+N1]
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


import mode_recovery
c, err = mode_recovery.recompose_DM(I,fm)

cn = c/c[0]
csoln = csol/csol[0]

obj1a = ndi.gaussian_filter(obj1.real, 2.) + 1j * ndi.gaussian_filter(obj1.imag, 2.)
frames = []
for i in range(50):
    f = np.fft.fftshift(abs(np.fft.fftn(random_mode(5., 5.)[ofs:-ofs,ofs:-ofs]*obj1a))**2)
    Itot = 10e7 * np.random.normal()**2
    frames.append(np.random.poisson(Itot*f/f.sum()))

frames = np.array(frames)
fmean = frames.mean(axis=0)

from pyE17 import utils as U
U.franzmap()


imshow(log(fmean+1)); draw()
