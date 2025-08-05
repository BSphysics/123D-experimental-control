# -*- coding: utf-8 -*-
"""
Created on Wed Jun 28 10:14:43 2023

@author: bs426
"""

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from py_pol.utils import degrees
import os

plt.close('all')

cwd = os.getcwd()

folders = next(os.walk(cwd))[1]
ellipticities= []
ellipseAngles= []

for folder in folders:
    files = os.listdir(cwd+'/' + folder)
    polariserAngles = np.load(cwd+'/' + folder +'/'+ files[1])
    powers = np.load(cwd+'/' + folder +'/'+ files[2])
    
    

    # polariserAngles = np.arange(0,180,jogStepDeg)
    fig = plt.figure(figsize = (12,6))
    ax = fig.add_subplot(121)
    plt.plot(polariserAngles,powers,'ro')
    plt.xlabel('Polariser Angle (deg)')
    
    from scipy.optimize import curve_fit
    
    def model_f(theta,p1,p2,p3,p4):
        
      return (p1*np.cos(theta*degrees-p3))**2 + (p2*np.sin(theta*degrees-p3))**2 + p4
    
    popt, pcov = curve_fit(model_f, polariserAngles, powers, bounds = ([0,0,0,0],[5,5,2*np.pi, 0.01]))
    
    Ex, Ey, alpha, offset = popt
    fittingAngles = np.arange(0,180,1)
    
    plt.plot(fittingAngles,model_f(fittingAngles, Ex, Ey, alpha, offset),'--b')
    
    print('\n Ellipse semi major axis angle = ' + str(np.round(alpha*180/np.pi)) + ' degrees \n')
    # print('Fitted Ex = ' + str(np.round(Ex,2)))
    # print('Fitted Ey = ' + str(np.round(Ey,2)))
    
    if Ex > Ey:
        a = Ex
        b = Ey
    else: 
        a = Ey
        b = Ex
    
    print('Ellipticity = '+ str(np.round(b/a,2)))
    ellipticities.append(np.round(b/a,3))
    ellipseAngles.append(np.round(alpha*180/np.pi,1))

plt.close('all')
es = np.array(ellipticities)*100
ea = np.array(ellipseAngles)

plt.plot(es, 'ro')
plt.title('Percentage ellipticity (Ex/Ey)*100 at time of calibration')
plt.xlabel('pSHG sequence step number')
plt.ylabel ('Fitted (Ex/Ey) *100')
plt.savefig('Percentage ellipticity.png')
# from matplotlib import patches
# # fig = plt.figure()
# ax = fig.add_subplot(122, aspect='auto')


# e1 = patches.Ellipse((0, 0), Emax, Emin,
#                  angle = alpha*180/np.pi, linewidth=2, fill = False, zorder=1)

# ax.add_patch(e1)
# ax.set_xlim([-0.5,0.5])
# ax.set_ylim([-0.5,0.5])
# # ax.axis('square')
# ax.axis('off')
# plt.title('Polarisation ellipse')

# print('Fitted Ex = ' + str(np.round(Emax,2)))
# print('Fitted Ey = ' + str(np.round(Emin,2)))