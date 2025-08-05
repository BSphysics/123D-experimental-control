# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 11:06:53 2023

@author: bs426
"""

import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
degrees = np.pi/180

polariserAngles = np.load('polariserAngles.npy')
powers = np.load('powers.npy')

fig = plt.figure(figsize = (12,6))
ax = fig.add_subplot(121)
plt.plot(polariserAngles,powers,'ro')
plt.xlabel('Polariser Angle (deg)')

def model_1(theta,p1,p2,p3):
  return (p1*np.cos(theta*degrees-p3))**2 + (p2*np.sin(theta*degrees-p3))**2

popt, pcov = curve_fit(model_1, polariserAngles, powers, bounds = ([-5,-5,0],[5,5,np.pi]))

Ex, Ey, alpha = popt
fittingAngles = np.arange(0,180,1)

plt.plot(fittingAngles,model_1(fittingAngles, Ex, Ey, alpha),'--b')



def model_2(alpha,p1,p2,p3,p4,p5,p6):
    
    I0 = p1
    gamma = p2
    HWP_offset = p3
    QWP_offset= p4
    linPolr_offset = p5
    delta = p6
    
    theta = 183 - HWP_offset
    phi = 149 - QWP_offset
    alpha = alpha - linPolr_offset
    
    d1 = -gamma*( np.cos(delta) * np.sin(phi*degrees) * np.sin(2*theta*degrees - phi*degrees) + np.sin(delta) * np.cos(phi*degrees) * np.cos(2*theta*degrees-phi*degrees))
    d2 = -gamma*( np.sin(delta) * np.sin(phi*degrees) * np.sin(2*theta*degrees - phi*degrees) - np.cos(delta) * np.cos(phi*degrees) * np.cos(2*theta*degrees-phi*degrees))
    d3 = np.sin(phi*degrees) * np.cos(2*theta*degrees - phi*degrees)
    d4 = np.cos(phi*degrees) * np.sin(2*theta*degrees - phi*degrees)
    
    I = I0 * ( (d1**2 + d2**2) * np.cos(alpha*degrees)**2 + (d3**2 + d4**2) * (np.sin(alpha*degrees)**2) + 2*(d1 * d3 + d2 * d4) * np.sin(alpha*degrees) * np.cos(alpha*degrees) )
    return I

ax = fig.add_subplot(122)
plt.plot(polariserAngles,powers,'ro')
plt.xlabel('Polariser Angle (deg)')


popt, pcov = curve_fit(model_2, polariserAngles, powers , bounds = ([0, 0, 0, 0, -np.pi, 0],[5, np.inf, np.pi/2, np.pi, np.pi, 2*np.pi]))

plt.plot(fittingAngles,model_2(fittingAngles, *popt),'--g')

print('HWP offset = ' + str(np.round(popt[2]*180/np.pi)))

print('QWP offset = ' + str(np.round(popt[3]*180/np.pi)))

print('LP offset = ' + str(np.round(popt[4]*180/np.pi)))


#%%
WP_diff = np.arange(0,180,1)
QWP_lin = 0.5*np.arctan(-np.tan(popt[5]) * np.sin(2 * WP_diff)) * 180/np.pi


