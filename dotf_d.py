# -*- coding: utf-8 -*-
"""
Created on Tue Dec 18 13:51:26 2018

@author: Kevin Devlin
"""

import numpy as np
import matplotlib.pyplot as plt
from skimage.restoration import unwrap_phase
import gaussian2d as g

#np.set_printoptions(threshold=np.nan)
#generate NxN Coordinate Grid

N = 1024                                #number of points
L = 1                                   #length of grid side (m)
delta = L/N                             #sample spacing
D = 0.20                                #aperture diameter
r = D/2                                 
f = 0.5                                 #focal length
f_n = f/D                               
wave = 1.0e-6                           #wavelength
k = 2*np.pi/wave                        #wavenumber

#coordinates
x = np.arange(-N/2, N/2)*delta
(xx, yy) = np.meshgrid(x, x)

#image freq coordinates
df = wave*f/(N*delta)                  #frequency spacing
fx = np.arange(-N/2, N/2)*df
fX, fY = np.meshgrid(fx, fx)



rho = np.sqrt(xx**2 + yy**2)
phi = np.arctan2(yy,xx)

#normalise co-ordinates
R_norm = rho/r

#MTFaxis = (N*delta)/wave/f_n

#generate aperture
outer_disc = np.zeros((N,N))
inner_disc = np.zeros((N,N))
obs=0.2

mask = (R_norm<=1)
mask2 = (R_norm<=(1*obs))
outer_disc[mask]=1
inner_disc[mask2]=1

aperture = outer_disc - inner_disc

#------------------------------------------------------------------------------
#Generate aberration
#------------------------------------------------------------------------------

rms = 0.1*wave
#w = np.sqrt(8)*(3*(R_norm**3)-2*R_norm)*np.sin(phi) *rms #Vertical Coma  
#w = 2*R_norm*np.sin(phi) *rms  #tilt
w = rms*np.sqrt(6)*(R_norm**2)*np.sin(phi) #astigmatism
#w = np.sqrt(3)*(2*R_norm**2-1) * rms #defocus

w[R_norm>1]=0

#------------------------------------------------------------------------------
#pupil plane A
#------------------------------------------------------------------------------

A_noab = aperture * np.exp(1j * k *0)
A = aperture * np.exp(1j * k *w)

#image plane B
B = np.fft.fftshift(np.fft.fft2(np.fft.fftshift(A)))*delta**2

PSF = np.abs(B)**2
PSF = PSF/np.max(PSF) 

#exit plane C
OTF = np.fft.ifftshift(np.fft.ifft2(np.fft.ifftshift(PSF)))
OTF = OTF/np.max(OTF)
MTF = np.abs(OTF)

#------------------------------------------------------------------------------
#pupil plane perturbations
#------------------------------------------------------------------------------

finger = np.zeros((N, N))
y_edge = r/delta + N/2 +1
x_edge = N/2 + 1

#finger[int(x_edge-1):int(x_edge), int(y_edge-1):int(y_edge)] = 1  #width*height

gauss = g.gaussian2d(N, 5, cent=(int(x_edge), int(y_edge)))

poke = np.exp(1j*k*gauss*wave*0.24)


perturbation = poke * aperture

#perturbation = aperture - finger
#perturbation = poke*aperture  #then do A + perturbation

#------------------------------------------------------------------------------
#second pupil plane
#------------------------------------------------------------------------------

A2 = A*perturbation
B2 = np.fft.fftshift(np.fft.fft2(np.fft.fftshift(A2)))*delta**2

PSF2 = np.abs(B2)**2
PSF2 = PSF2/np.max(PSF2)

OTF2 = np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(PSF2)))
OTF2 = OTF2/np.max(OTF2)

MTF2 = np.abs(OTF2)

#differential optical trasfer function
dOTF = OTF - OTF2

amp = np.abs(dOTF)
phase = np.angle(dOTF)

#unwrap phase

#------------------------------------------------------------------------------
#masking and phase unwrapping
#------------------------------------------------------------------------------

m1 = np.roll(aperture, -int((r)/delta))
m2 = np.roll(aperture, int((r)/delta))


dOTF_mask = m1
masked_phase = phase * dOTF_mask
dOTF_mask[dOTF_mask>1] = 1

#scikit image unwrap phase method
unwrapped_phase = unwrap_phase((np.angle(dOTF)*dOTF_mask))
#unwrapped_phase = np.unwrap((np.angle(dOTF)*dOTF_mask))

unwrapped_phase = np.roll(unwrapped_phase, int(r/delta))

input_phase = unwrap_phase(np.angle(A))
#input_phase = np.unwrap(np.angle(A))

#------------------------------------------------------------------------------
#Statistics
#------------------------------------------------------------------------------
#circ = perturbation.astype(bool)
circ = aperture.astype(bool)

RMS_input  = np.std(input_phase[circ]) *1/k *1e9
print("RMS_input (nm):", RMS_input)

RMS_output = np.std((unwrapped_phase)[circ]) *1/k * 1e9
print("RMS_out (nm): ", RMS_output)

residual = (input_phase - unwrapped_phase)*aperture

RMS_residual = np.std(residual[circ]) /k *1e9
print("RMS_residual (nm): ", RMS_residual) 


#------------------------------------------------------------------------------
#data visualisation
#------------------------------------------------------------------------------

fig1 = plt.figure(figsize=(8,4))
plt.subplot(121)
plt.imshow(unwrap_phase(np.angle(A)), extent = [x[0], x[-1], x[0], x[-1]])
plt.title('input pupil')
plt.gca().set_xlim(-0.2, 0.2)
plt.gca().set_ylim(-0.2, 0.2)
plt.xlabel('x, (m)')
plt.ylabel('y, (m)')
plt.colorbar()


plt.subplot(122)
plt.imshow(unwrap_phase(np.angle(A2)), extent = [x[0], x[-1], x[0], x[-1]])
plt.title('perturbed input pupil')
plt.gca().set_xlim(-0.2, 0.2)
plt.gca().set_ylim(-0.2, 0.2)
plt.xlabel('x, (m)')
plt.ylabel('y, (m)')
plt.colorbar()

plt.tight_layout()
plt.show()


fig4 = plt.figure()
plt.imshow(np.abs(dOTF))
plt.title('dOTF')
plt.colorbar()

fig5 = plt.figure()
plt.imshow(np.angle(dOTF)*(m1+m2))
plt.title('dOTF phase')
plt.colorbar()

fig6 = plt.figure()
plt.imshow(unwrapped_phase, extent = [x[0], x[-1], x[0], x[-1]])
plt.gca().set_xlim(-0.2, 0.2)
plt.gca().set_ylim(-0.2, 0.2)
plt.title('unwrapped phase')
plt.colorbar()

fig6 = plt.figure()
plt.imshow(residual, extent = [x[0], x[-1], x[0], x[-1]])
plt.gca().set_xlim(-0.2, 0.2)
plt.gca().set_ylim(-0.2, 0.2)
plt.title('residual wavefront error')
plt.colorbar()




'''
##
fig2 = plt.figure(figsize=(12,6))
plt.subplot(121)
plt.imshow((PSF), extent=[fx[0], fx[-1], fx[0], fx[-1]])
plt.title('PSF')
plt.xlabel('x (m)')
plt.ylabel('y (m)')
plt.gca().set_xlim(-50e-6, 50e-6)
plt.gca().set_ylim(-50e-6, 50e-6)
plt.colorbar()

plt.subplot(122)
plt.imshow(PSF2, extent = [fx[0], fx[-1], fx[0], fx[-1]])
plt.title('perturbed PSF')
plt.xlabel('x (m)')
plt.ylabel('y (m)')
plt.gca().set_xlim(-50e-6, 50e-6)
plt.gca().set_ylim(-50e-6, 50e-6)
plt.colorbar()

plt.tight_layout()
plt.show()

fig3 = plt.figure(figsize=(12,6))
plt.subplot(121)
plt.imshow(np.real(OTF/np.max(OTF)))
plt.title('OTF')
plt.xlabel('pixels')
plt.ylabel('pixels')
plt.colorbar()

plt.subplot(122)
plt.imshow(np.real(OTF2/np.max(OTF2)))
plt.title('OTF2')
plt.xlabel('pixels')
plt.ylabel('pixels')
plt.colorbar()

plt.tight_layout()
plt.show()

fig3 = plt.figure()
plt.imshow(MTF)
plt.title('Modulation Transfer Function')
plt.colorbar()

##
'''



