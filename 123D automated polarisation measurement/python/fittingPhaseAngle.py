# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 10:26:32 2023

@author: bs426
"""

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from py_pol.jones_vector import Jones_vector
from py_pol.utils import degrees

# plt.close('all')

foldername = r'C:\Users\bs426\OneDrive - University of Exeter\!Work\Work.2023\Lab 2023\123D\2023_06_20 ellipticity measurements\HWP = 030 deg __ QWP = 094 deg'
polariserAngles = np.load(foldername + '\\polariserAngles.npy')
powers = np.load(foldername + '\\powers.npy')
# powers = powers / np.max(powers)
plt.close('all')
plt.figure(1)
plt.plot(polariserAngles , powers , 'ro')

alphas = (np.arange(-20,180,1)) * degrees

theta = (30+82) * degrees

delta = 60 * degrees
mPhaseAngle = 68 * degrees

tilt = 0*degrees

res = []
for alpha in alphas:
    hwp1 = np.array( [[np.cos(2*theta) , np.sin(2*theta)] , [np.sin(2*theta) , -np.cos(2*theta)]] )
 
    microscope1 = np.array([[np.cos(delta/2) + 1j*np.sin(delta/2)*np.cos(2*mPhaseAngle) , 1j*np.sin(delta/2) * np.sin(2*mPhaseAngle)],
                      [1j*np.sin(delta/2) * np.sin(2*mPhaseAngle) , np.cos(delta/2)-1j*np.sin(delta/2)*np.cos(2*mPhaseAngle)]])

    e0 = np.array([[np.cos(tilt)] , [np.sin(tilt)]])

    e1 = np.round(np.matmul(hwp1 , e0),3)

    e2 = np.round(np.matmul(microscope1 , e1),3)
      
    linearPolariser1 = np.array([[np.cos(alpha)**2 , np.sin(alpha) * np.cos(alpha)],
                                 [np.sin(alpha) * np.cos(alpha) , np.sin(alpha)**2]])
    
   
    e3 = np.round(np.matmul(linearPolariser1 , e2),3)
    jn = Jones_vector("jn")
    jn.from_matrix(e3)
    
           
    intensity = jn.parameters.intensity()
   
    res.append(intensity * 0.63)

plt.plot(alphas / degrees  + 20, res , '--b')
plt.title('HWP = ' + str(np.round(theta/degrees)) + ', Fitted delta = ' + str(np.round(delta/degrees)) + ', fitted phase angle = ' + str(np.round(mPhaseAngle/degrees)))

# def model_p(alphas, delta, mPhaseAngle):
    
#     # theta,alphas = angles
#     # theta = theta * degrees 
#     alphas = alphas*degrees
#     theta = 0*degrees
    
#     # print(len(alphas))
#     res = []
#     for alpha in alphas:
#         hwp1 = np.array( [[np.cos(2*theta) , np.sin(2*theta)] , [np.sin(2*theta) , -np.cos(2*theta)]] )
     
#         microscope1 = np.array([[np.cos(delta/2) + 1j*np.sin(delta/2)*np.cos(2*mPhaseAngle) , 1j*np.sin(delta/2) * np.sin(2*mPhaseAngle)],
#                           [1j*np.sin(delta/2) * np.sin(2*mPhaseAngle) , np.cos(delta/2)-1j*np.sin(delta/2)*np.cos(2*mPhaseAngle)]])
    
#         e0 = np.array([[1] , [0]])
    
#         e1 = np.round(np.matmul(hwp1 , e0),3)
    
#         e2 = np.round(np.matmul(microscope1 , e1),3)
          
#         linearPolariser1 = np.array([[np.cos(alpha)**2 , np.sin(alpha) * np.cos(alpha)],
#                                      [np.sin(alpha) * np.cos(alpha) , np.sin(alpha)**2]])
        
       
#         e3 = np.round(np.matmul(linearPolariser1 , e2),3)
#         jn = Jones_vector("jn")
#         jn.from_matrix(e3)
        
               
#         intensity = jn.parameters.intensity()
#         # print(intensity)
#         res.append(intensity)
#     return res

# from scipy.optimize import curve_fit


# popt, pcov = curve_fit(model_p, polariserAngles, powers)

# deltaFit, mPhaseAngleFit = popt
# fittingAngles = np.arange(0,180,1)

# plt.plot(fittingAngles,model_p(fittingAngles, deltaFit, mPhaseAngleFit),'--b')


