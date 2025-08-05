# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 10:02:55 2023

@author: bs426
"""

import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
# import matplotlib.pyplot as plt
# from scipy.optimize import curve_fit

delta = 45 * np.pi/180
gamma = 0.6
theta = 60 * np.pi/180

beta = np.arctan( (gamma**2 - np.tan(theta)**2 + np.sqrt(gamma**4 + np.tan(theta)**4 + 2 * gamma**2 * np.cos(2*delta) * np.tan(theta)**2)) / (-2 * gamma * np.cos(delta) * np.tan(theta)) )

alpha = beta + np.arctan( 1 + np.sqrt( 1 + np.sin(2*beta)**2 * np.tan(delta)**2) / (np.sin(2*beta) * np.tan(delta))) 

print('QWP angle = ' + str(np.round(beta * 180/np.pi)))

print('HWP angle = ' + str(np.round(alpha / 2 * 180/np.pi)))

#%% Try to model results - should get a linear polarisation 

phi = alpha - beta

d1 = np.cos(beta) * np.cos(phi)

d2 = -np.sin(beta) * np.sin(phi)

d3 = gamma * (np.sin(beta) * np.cos(phi) * np.cos(delta) - np.cos(beta) * np.sin(phi) * np.sin(delta)) 

d4 = gamma * (np.sin(beta) * np.cos(phi) * np.sin(delta) + np.cos(beta) * np.sin(phi) * np.cos(delta))

Ex = (d1 + 1j*d2)

Ey = (d3 + 1j*d4)

# print(np.round(d3/d1,3))
# print(np.round(d4/d2,3))


#%%
import matplotlib.pyplot as plt
plt.close('all')
# angle = 30 * np.pi/180
angle = alpha/2

hwp = np.array( [[np.cos(2*angle) , np.sin(2*angle)] , [np.sin(2*angle) , -np.cos(2*angle)]] )

# angle = 60 * np.pi/180
angle = beta
qwp = np.array( [[np.cos(angle)**2 + 1j*np.sin(angle)**2 , (1-1j)*np.sin(angle)*np.cos(angle)] , [(1-1j)*np.sin(angle)*np.cos(angle) , np.sin(angle)**2+ 1j*np.cos(angle)**2]] )


angle = 0 * np.pi/180
# delta = 0 * np.pi/180
retarder = np.array( [[np.cos(angle)**2 + np.sin(angle)**2 * np.exp(-1j * delta) , np.sin(angle)*np.cos(angle) - np.sin(angle)*np.cos(angle) * np.exp(-1j * delta)] , [ np.sin(angle)*np.cos(angle) - np.sin(angle)*np.cos(angle) * np.exp(-1j * delta) , np.sin(angle)**2 + np.cos(angle)**2 * np.exp(-1j * delta)]] )


e0 = np.array([[1] , [0]])

e1 = np.round(np.matmul(hwp , e0),3)

e2 = np.round(np.matmul(qwp , e1),3)

e3 = np.round(np.matmul(retarder , e2),3)

print(e3)

from py_pol.jones_vector import Jones_vector
from py_pol.jones_matrix import Jones_matrix
from py_pol.utils import degrees




j0 = Jones_vector("j0")
j0.linear_light(azimuth = (0) * degrees)

hwp = Jones_matrix("hwp")
hwp.half_waveplate(azimuth = alpha /2)

qwp = Jones_matrix("qwp")
qwp.quarter_waveplate(azimuth = beta)



# linPol = Jones_matrix("linPol")
# linPol.diattenuator_perfect(azimuth = (0 + offset) * degrees)

microscope = Jones_matrix("Retarder")
microscope.retarder_linear(R = delta, azimuth = 0*degrees)

j1 = microscope*qwp*hwp*j0

print(j1)
j1.draw_ellipse()


#%%
plt.close('all')
theta = []
phi = []
delta = []

j0 = Jones_vector("j0")
j0.linear_light(azimuth = (0) * degrees)


theta = 30 * degrees
hwp = Jones_matrix("hwp")
hwp.half_waveplate(azimuth = theta)

phi = 45 * degrees
qwp = Jones_matrix("qwp")
qwp.quarter_waveplate(azimuth = phi)


delta = 28 * degrees
microscope = Jones_matrix("Retarder")
microscope.retarder_linear(R = delta, azimuth = 0 * degrees)

j1 = microscope*qwp*hwp*j0

alpha = 0 * degrees

pol =  np.array([[np.cos(alpha)] , [np.sin(alpha)]]) 

phiArr = np.arange(0,180,0.1) * degrees
thetaArr = np.arange(0,90,0.1) * degrees
res=[]
for theta in thetaArr:
    print(np.round(theta*180/np.pi))
    for phi in phiArr:
      
        hwp1 = np.array( [[np.cos(2*theta) , np.sin(2*theta)] , [np.sin(2*theta) , -np.cos(2*theta)]] )
        
        qwp1 = np.array([[np.cos(np.pi/4) + 1j*np.sin(np.pi/4)*np.cos(2*phi) , 1j*np.sin(np.pi/4) * np.sin(2*phi)],
                         [1j*np.sin(np.pi/4) * np.sin(2*phi) , np.cos(np.pi/4)-1j*np.sin(np.pi/4)*np.cos(2*phi)]])
        
        
        mPhaseAngle = 0 * degrees                  
        microscope1 = np.array([[np.cos(delta/2) + 1j*np.sin(delta/2)*np.cos(2*mPhaseAngle) , 1j*np.sin(delta/2) * np.sin(2*mPhaseAngle)],
                         [1j*np.sin(delta/2) * np.sin(2*mPhaseAngle) , np.cos(delta/2)-1j*np.sin(delta/2)*np.cos(2*mPhaseAngle)]])
        
        
        e0 = np.array([[1] , [0]])
        
        
        e1 = np.round(np.matmul(hwp1 , e0),3)
        
        e2 = np.round(np.matmul(qwp1 , e1),3)
        
        e3 = np.round(np.matmul(microscope1 , e2),3)
        
        e4 = e3   

        res.append((e4))



res = np.asarray(res)
#%%
res1 = np.reshape(res[:,0,0], (900,1800))
res2 = np.reshape(res[:,1,0], (900,1800))

res1phase = np.angle(res1)
res2phase = np.angle(res2)

phasediff = np.abs(res1phase - res2phase)

plt.imshow(phasediff, origin='lower')

#%% For every QWP angle, find the HWP angle that produces a minimum 

hwpMin = []
for idx in range(0,1800):
    hwpMin.append(np.argmin(phasediff[:,idx]))

tweak1 = np.zeros(900)
tweak2 = np.ones(900)+44

tweak = np.append(tweak1,tweak2)

hwpMin = np.array(hwpMin)/10 + tweak

 
qwpMin = np.arange(0,1800)/10   
    
plt.figure(99)
plt.plot(qwpMin, hwpMin, 'ro')


#%% CHECK - This is working! 

theta = 67 * degrees
phi = 120 * degrees


hwp1 = np.array( [[np.cos(2*theta) , np.sin(2*theta)] , [np.sin(2*theta) , -np.cos(2*theta)]] )

qwp1 = np.array([[np.cos(np.pi/4) + 1j*np.sin(np.pi/4)*np.cos(2*phi) , 1j*np.sin(np.pi/4) * np.sin(2*phi)],
                 [1j*np.sin(np.pi/4) * np.sin(2*phi) , np.cos(np.pi/4)-1j*np.sin(np.pi/4)*np.cos(2*phi)]])
                 
microscope1 = np.array([[np.cos(delta/2) + 1j*np.sin(delta/2)*np.cos(2*mPhaseAngle) , 1j*np.sin(delta/2) * np.sin(2*mPhaseAngle)],
                 [1j*np.sin(delta/2) * np.sin(2*mPhaseAngle) , np.cos(delta/2)-1j*np.sin(delta/2)*np.cos(2*mPhaseAngle)]])


e0 = np.array([[1] , [0]])


e1 = np.round(np.matmul(hwp1 , e0),3)

e2 = np.round(np.matmul(qwp1 , e1),3)

e3 = np.round(np.matmul(microscope1 , e2),3)

e4 = e3  



jn = Jones_vector("j0")
jn.from_matrix(e4)

ellipAxes = jn.parameters.ellipse_axes()

print('Angle of semi major axis = ' + str(np.round(jn.parameters.azimuth()*180/np.pi,2)) + ' degrees')
print('Ellipticity = ' + str( np.round(ellipAxes[1] / ellipAxes[0] , 2 )))
print('py_pol degree of linear polarisation = ' + str(np.round(jn.parameters.degree_linear_polarization(),4)))
      
# linPolAngle.append(np.round(jn.parameters.azimuth()*180/np.pi,2))

#%% 
linPolAngle = []
degreeLinearPol = []

for idx in range(0,1800,1):
    print()
    theta = hwpMin[idx] * degrees
    phi = qwpMin[idx] * degrees
    
    
    hwp1 = np.array( [[np.cos(2*theta) , np.sin(2*theta)] , [np.sin(2*theta) , -np.cos(2*theta)]] )
    
    qwp1 = np.array([[np.cos(np.pi/4) + 1j*np.sin(np.pi/4)*np.cos(2*phi) , 1j*np.sin(np.pi/4) * np.sin(2*phi)],
                     [1j*np.sin(np.pi/4) * np.sin(2*phi) , np.cos(np.pi/4)-1j*np.sin(np.pi/4)*np.cos(2*phi)]])
                     
    microscope1 = np.array([[np.cos(delta/2) + 1j*np.sin(delta/2)*np.cos(2*mPhaseAngle) , 1j*np.sin(delta/2) * np.sin(2*mPhaseAngle)],
                     [1j*np.sin(delta/2) * np.sin(2*mPhaseAngle) , np.cos(delta/2)-1j*np.sin(delta/2)*np.cos(2*mPhaseAngle)]])
    
    
    e0 = np.array([[1] , [0]])
    
    
    e1 = np.round(np.matmul(hwp1 , e0),3)
    
    e2 = np.round(np.matmul(qwp1 , e1),3)
    
    e3 = np.round(np.matmul(microscope1 , e2),3)
    
    e4 = e3  
    
    
    
    jn = Jones_vector("j0")
    jn.from_matrix(e4)
    
    ellipAxes = jn.parameters.ellipse_axes()
    
    # print('Angle of semi major axis = ' + str(np.round(jn.parameters.azimuth()*180/np.pi,2)) + ' degrees')
    # print('Ellipticity = ' + str( np.round(ellipAxes[1] / ellipAxes[0] , 2 )))
    # print('py_pol degree of linear polarisation = ' + str(np.round(jn.parameters.degree_linear_polarization(),4)))
          
    linPolAngle.append(np.round(jn.parameters.azimuth()*180/np.pi,2))
    degreeLinearPol.append(np.round(jn.parameters.degree_linear_polarization(),6))
    

linPolAngle = np.asarray(linPolAngle)
degreeLinearPol = np.asarray(degreeLinearPol)

#%%
plt.figure(100)
plt.plot(hwpMin[1:], np.round(linPolAngle[1:]))
plt.xlabel('HWP angle (deg)')
plt.ylabel('Linear Polarisation angle')

#%% This is now nicely working - assumming we know the phase delay of the microscope, we can generate a look up table thats tells which which HWP and QWPangles are needed
# to create a linear polarisation TODO: Tidy up. 

lpa = np.round(linPolAngle[1:])

a = np.where(lpa == 15)
middle = int(a[0].shape[0]/2)

index = a[0][middle]

hwpMin[index]
qwpMin[index]

#%%

lpa = np.round(linPolAngle[1:])

linPolVals = np.arange(0,181,15)

hwpVals = []
qwpVals = []

for lp in linPolVals:
    a = np.where(lpa == lp)
    middle = int(a[0].shape[0]/2)

    index = a[0][middle]

    hwpVals.append(hwpMin[index])
    qwpVals.append(qwpMin[index])


np.save('linPolVals', linPolVals)
np.save('hwpVals', hwpVals)
np.save('qwpVals', qwpVals)
