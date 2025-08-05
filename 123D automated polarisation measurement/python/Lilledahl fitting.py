# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 13:03:55 2023

@author: bs426
"""

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import os
from py_pol.jones_vector import Jones_vector
from py_pol.jones_matrix import Jones_matrix
from py_pol.utils import degrees

cwd = os.getcwd()

folder = r'C:\Users\bs426\OneDrive - University of Exeter\!Work\Work.2023\Lab 2023\123D\Polarisation measurements\2023_06_29\2023_6_29_1041\000 HWP = 20  QWP = 155'
files = os.listdir(folder)
polariserAngles = np.load(folder +'/'+ files[1])*np.pi/180
# powers = np.load( folder +'/'+ files[2])
plt.close('all')

angles = np.arange(0,361)

j0 = Jones_vector("j0")
j0.linear_light(azimuth = 0 * degrees)

hwp = Jones_matrix("hwp")
hwp.half_waveplate(azimuth = 0 * degrees)

qwp = Jones_matrix("qwp")
qwp.quarter_waveplate(azimuth = 0 * degrees)

microscopePhase = 90 * degrees
microscope = Jones_matrix("Retarder")
microscope.retarder_linear(R = microscopePhase, azimuth = 45 * degrees)

linearPolariser = Jones_matrix('Polarizer')
linearPolariser.diattenuator_perfect(azimuth = polariserAngles)

j1 = linearPolariser*microscope*hwp*qwp*j0

powers = j1.parameters.intensity()



#%%

def polfit(alpha, gamma, delta, theta, phi, I0):

    d1 = -1*(np.cos(delta)*np.sin(phi)*np.sin(2*theta-phi) + np.sin(delta)*np.cos(phi)*np.cos(2*theta-phi))
    
    d2 = -1*(np.sin(delta)*np.sin(phi)*np.sin(2*theta-phi) - np.cos(delta)*np.cos(phi)*np.cos(2*theta-phi))
    
    d3 = np.sin(phi)*np.cos(2*theta-phi)

    d4 = np.cos(phi)*np.sin(2*theta-phi)
    
    Ex = (d1 + 1j*d2)
    Ey = (d3 + 1j*d4)
    
    # Ipol = I0 * abs(Ex * np.conj(Ex) * np.cos(alpha)**2 + Ey * np.conj(Ey) * np.sin(alpha)**2 + (Ex * np.conj(Ey) + Ey * np.conj(Ex)) * np.sin(alpha) * np.cos(alpha) )
    Ipol = I0*((d1**2 + d2**2)*(np.cos(alpha)**2) + (d3**2 + d4**2)*(np.sin(alpha)**2) + 2*(d1*d3 + d2*d4)*np.sin(alpha)*np.cos(alpha))
    
    return Ipol


fig = plt.figure(figsize = (12,6))
ax = fig.add_subplot(111)
plt.plot(polariserAngles*180/np.pi,powers,'ro')
plt.xlabel('Polariser Angle (deg)')

from scipy.optimize import curve_fit

popt, pcov = curve_fit(polfit, polariserAngles, powers, bounds = ((0, -np.inf, -np.inf, -np.inf, np.max(powers)*0.9), (0.1, np.inf, np.inf, np.inf, np.max(powers)*1.1)))


fittingAngles = np.arange(0,np.pi,0.01)

gamma, delta, theta, phi, I0 = popt

# plt.plot(fittingAngles*180/np.pi , polfit(fittingAngles, gamma, delta, theta, phi, I0),'--b')
# 
print('\n Gamma = ' + str(np.round(gamma,2)))
print('\n delta = ' + str(np.round(delta*180/np.pi,2)))
print('\n theta (HWP angle) = ' + str(np.round(theta*180/np.pi,2)))
print('\n phi (QWP angle) = ' + str(np.round(phi*180/np.pi,2)))
print('\n I0 = ' + str(np.round(I0,2)))