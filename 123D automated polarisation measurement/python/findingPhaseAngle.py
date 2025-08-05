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

theta = 60 * degrees
phi = 215 * degrees
delta = 8 * degrees
mPhaseAngle = 48 * degrees


hwp1 = np.array( [[np.cos(2*theta) , np.sin(2*theta)] , [np.sin(2*theta) , -np.cos(2*theta)]] )

qwp1 = np.array([[np.cos(np.pi/4) + 1j*np.sin(np.pi/4)*np.cos(2*phi) , 1j*np.sin(np.pi/4) * np.sin(2*phi)],
                  [1j*np.sin(np.pi/4) * np.sin(2*phi) , np.cos(np.pi/4)-1j*np.sin(np.pi/4)*np.cos(2*phi)]])
                 
microscope1 = np.array([[np.cos(delta/2) + 1j*np.sin(delta/2)*np.cos(2*mPhaseAngle) , 1j*np.sin(delta/2) * np.sin(2*mPhaseAngle)],
                 [1j*np.sin(delta/2) * np.sin(2*mPhaseAngle) , np.cos(delta/2)-1j*np.sin(delta/2)*np.cos(2*mPhaseAngle)]])

tilt = 82 *degrees

e0 = np.array([[np.cos(tilt)] , [np.sin(tilt)]])

e1 = np.round(np.matmul(hwp1 , e0),3)

e2 = np.round(np.matmul(qwp1 , e1),3)

e3 = np.round(np.matmul(microscope1 , e2),3)

jn = Jones_vector("jn")
jn.from_matrix(e3)

jn.draw_ellipse()

# intensities = []
# for alpha in range(0,200,10):
#     alpha = alpha*degrees
#     linearPolariser1 = np.array([[np.cos(alpha)**2 , np.sin(alpha) * np.cos(alpha)],
#                                  [np.sin(alpha) * np.cos(alpha) , np.sin(alpha)**2]])
    
#     e4 = np.round(np.matmul(linearPolariser1 , e3),3)
    
    
#     jn = Jones_vector("jn")
#     jn.from_matrix(e4)
    
#     ellipAxes = jn.parameters.ellipse_axes()
    
#     intensity = jn.parameters.intensity()
#     intensities.append(intensity)

# polariserAngles = np.arange(0,200,10)
# plt.plot(polariserAngles , intensities , 'ro')

# print('Ellipticity = ' + str( np.round(ellipAxes[1] / ellipAxes[0] , 2 )))
# print('py_pol degree of linear polarisation = ' + str(np.round(jn.parameters.degree_linear_polarization(),4)))

# print('\nCalculated angle of semi major axis = ' + str(np.round(jn.parameters.azimuth()*180/np.pi,0)) + ' degrees')

# #%%
linearPolariser1 = []
#%%
def model_p(alphas, delta, mPhaseAngle):
    
    # theta,alphas = angles
    # theta = theta * degrees 
    alphas = alphas*degrees
    theta = 10*degrees
    
    # print(len(alphas))
    res = []
    for alpha in alphas:
        hwp1 = np.array( [[np.cos(2*theta) , np.sin(2*theta)] , [np.sin(2*theta) , -np.cos(2*theta)]] )
     
        microscope1 = np.array([[np.cos(delta/2) + 1j*np.sin(delta/2)*np.cos(2*mPhaseAngle) , 1j*np.sin(delta/2) * np.sin(2*mPhaseAngle)],
                          [1j*np.sin(delta/2) * np.sin(2*mPhaseAngle) , np.cos(delta/2)-1j*np.sin(delta/2)*np.cos(2*mPhaseAngle)]])
    
        e0 = np.array([[1] , [0]])
    
        e1 = np.round(np.matmul(hwp1 , e0),3)
    
        e2 = np.round(np.matmul(microscope1 , e1),3)
          
        linearPolariser1 = np.array([[np.cos(alpha)**2 , np.sin(alpha) * np.cos(alpha)],
                                     [np.sin(alpha) * np.cos(alpha) , np.sin(alpha)**2]])
        
       
        e3 = np.round(np.matmul(linearPolariser1 , e2),3)
        jn = Jones_vector("jn")
        jn.from_matrix(e3)
        
               
        intensity = jn.parameters.intensity()
        print(intensity)
        res.append(intensity)
    return res

from scipy.optimize import curve_fit

polariserAngles = np.arange(0,200,10)
# hwpAngles = np.repeat(10,20)

popt, pcov = curve_fit(model_p, polariserAngles, intensities)

deltaFit, mPhaseAngleFit = popt
fittingAngles = np.arange(0,180,1)

plt.plot(fittingAngles,model_p(fittingAngles, deltaFit, mPhaseAngleFit),'--b')

#%%

a = np.ones([2, 2, 20])

b= np.squeeze(np.array([e0,e0,e0,e0,e0,e0,e0,e0,e0,e0,e0,e0,e0,e0,e0,e0,e0,e0,e0,e0]))

c = np.squeeze(np.ones([20,2,1]))


np.matmul(a, b).shape

