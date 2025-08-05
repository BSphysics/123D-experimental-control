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

plt.close('all')
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18,4))
alphas = (np.arange(-20,180,1)) * degrees

foldername = r'D:\123D scripts\Parallel ELL and Arduino control\polPython\HWP = 082 __ QWP = 198'
polariserAngles = np.load(foldername + '\\polariserAngles.npy')
powers = np.load(foldername + '\\powers.npy')

polTweak=30
ax1.plot(polariserAngles - polTweak, powers , 'ro')


theta = (0) * degrees

delta = 56 * degrees
mPhaseAngle = 58 * degrees

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
   
    res.append(intensity * 0.61)

ax1.plot(alphas / degrees  + 0, res , '--b')
ax1.set_title('HWP = ' + str(np.round(theta/degrees)) + ', delta = ' + str(np.round(delta/degrees)) + ', phase angle = ' + str(np.round(mPhaseAngle/degrees)))

foldername = r'D:\123D scripts\Parallel ELL and Arduino control\polPython\HWP = 092 __ QWP = 218'
polariserAngles = np.load(foldername + '\\polariserAngles.npy')
powers = np.load(foldername + '\\powers.npy')

ax2.plot(polariserAngles- polTweak , powers , 'ro')


theta = (10) * degrees

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
   
    res.append(intensity * 0.61)

ax2.plot(alphas / degrees  + 0, res , '--b')
ax2.set_title('HWP = ' + str(np.round(theta/degrees)) + ', delta = ' + str(np.round(delta/degrees)) + ', phase angle = ' + str(np.round(mPhaseAngle/degrees)))


foldername = r'D:\123D scripts\Parallel ELL and Arduino control\polPython\HWP = 122 __ QWP = 278'
polariserAngles = np.load(foldername + '\\polariserAngles.npy')
powers = np.load(foldername + '\\powers.npy')

ax3.plot(polariserAngles- polTweak , powers , 'ro')


theta = (40) * degrees

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

ax3.plot(alphas / degrees  + 0, res , '--b')
ax3.set_title('HWP = ' + str(np.round(theta/degrees)) + ', delta = ' + str(np.round(delta/degrees)) + ', phase angle = ' + str(np.round(mPhaseAngle/degrees)))
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


