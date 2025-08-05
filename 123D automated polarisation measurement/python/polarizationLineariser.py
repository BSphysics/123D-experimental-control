# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 15:52:16 2023
@author: bs426

Code for calculating the angles of QWP and HWP needed to produce a linear polairsaiton at a particular angle. 

The code calculates the matrix of input polarisation (assummed to be linear e.g. [1,0]) * HWP * QWP * microscope 
where the microscope is assummed to be a linear retarder (no diattenuation in this version) with a known phase retardance (delta)
at an angle of 0 degrees from the x axis. 

The result of the this matrix multiplication is then evaluated at every HWP and QWP angle (in increments of 0.1 degrees - so it takes around a minute)

The result is an array of 1800 2x1 vectors (each vector is [Ex,Ey]). Then we use the fact that linear polarisation has zero phase shift between Ex and Ey

and calucalte the phase angle of each Ex and Ey, and subtract them. By looking at where the absolute value of this difference in phase angle is a minimum, we 
find the combination of HWP and QWP angles that produce linear polairsation. 

The last step is to work out what angle of linear polairsation is produced for each combination of HWP and QWP angles. For this we take the angles of HWP and QWP 
that correspond to linear polairsation, put them back into the matrix multiplication e.g. microscope*qwp*hwp*E0 and turn the resulting vecotr into a Jones vector
Then use py_pol to calculate the properties of the Jones vector. The polarisation angle is ont regularly samples so to make sure we get good values for the polarisation values 
that we need in the experiment e.g. 0,15,30,45,60 etc, a quick bit of simple sampling is done. The linear polairsation angle, HWP angles and QWP angles are all saved to .npy file. 


TODO: Check if I have enough measurements to calculate delta already. 

TODO: there will be an issue of figuring out the offsets between the fast axes of the waveplates, and the motors of the rotation stages. Lilledhal 2018 may help with this. 


"""


import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from py_pol.jones_vector import Jones_vector
from py_pol.utils import degrees

plt.close('all')


delta = 46 * degrees # The phase retardance of the microscope components

alpha = 0 * degrees

pol =  np.array([[np.cos(alpha)] , [np.sin(alpha)]]) 

phiArr = np.arange(0,180,0.1) * degrees
thetaArr = np.arange(0,90,0.1) * degrees
res=[]

for theta in thetaArr:
    
    for phi in phiArr:
      
        hwp1 = np.array( [[np.cos(2*theta) , np.sin(2*theta)] , [np.sin(2*theta) , -np.cos(2*theta)]] )
        
        qwp1 = np.array([[np.cos(np.pi/4) + 1j*np.sin(np.pi/4)*np.cos(2*phi) , 1j*np.sin(np.pi/4) * np.sin(2*phi)],
                         [1j*np.sin(np.pi/4) * np.sin(2*phi) , np.cos(np.pi/4)-1j*np.sin(np.pi/4)*np.cos(2*phi)]])
        
        
        mPhaseAngle = 58 * degrees                  
        microscope1 = np.array([[np.cos(delta/2) + 1j*np.sin(delta/2)*np.cos(2*mPhaseAngle) , 1j*np.sin(delta/2) * np.sin(2*mPhaseAngle)],
                         [1j*np.sin(delta/2) * np.sin(2*mPhaseAngle) , np.cos(delta/2)-1j*np.sin(delta/2)*np.cos(2*mPhaseAngle)]])
        
        
        e0 = np.array([[1] , [0]])
        
        
        e1 = np.round(np.matmul(hwp1 , e0),3)
        
        e2 = np.round(np.matmul(qwp1 , e1),3)
        
        e3 = np.round(np.matmul(microscope1 , e2),3)
        
        e4 = e3   

        res.append((e4))



res = np.asarray(res)

res1 = np.reshape(res[:,0,0], (900,1800))
res2 = np.reshape(res[:,1,0], (900,1800))

res1phase = np.angle(res1)
res2phase = np.angle(res2)

phasediff = np.abs(res1phase - res2phase)

#%% For every QWP angle, find the HWP angle that produces a minimum 

hwpMin = []
for idx in range(0,1800):
    hwpMin.append(np.argmin(phasediff[:,idx]))

tweak1 = np.zeros(900)
tweak2 = np.ones(900)+44

tweak = np.append(tweak1,tweak2)

hwpMin = np.array(hwpMin)/10 + tweak

 
qwpMin = np.arange(0,1800)/10  

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
          
    linPolAngle.append(np.round(jn.parameters.azimuth()*180/np.pi,2))
    degreeLinearPol.append(np.round(jn.parameters.degree_linear_polarization(),6))
    

linPolAngle = np.asarray(linPolAngle)
degreeLinearPol = np.asarray(degreeLinearPol)

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

#%%
import pandas as pd

polData = np.array([hwpVals , qwpVals , linPolVals]).T
df = pd.DataFrame (polData)

## save to xlsx file
filepath = 'Calculated polarization settings.xlsx'

df.to_excel(filepath, index=False)

#%% CHECK - Put the calculated values for HWP and QWP angle back through and check they produce a linear polarisation at the expected angle 

idx = np.random.randint(len(linPolVals))
theta = hwpVals[idx] * degrees
phi = qwpVals[idx] * degrees


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



jn = Jones_vector("jn")
jn.from_matrix(e4)

ellipAxes = jn.parameters.ellipse_axes()

print('Ellipticity = ' + str( np.round(ellipAxes[1] / ellipAxes[0] , 2 )))
print('py_pol degree of linear polarisation = ' + str(np.round(jn.parameters.degree_linear_polarization(),4)))

print('\nCalculated angle of semi major axis = ' + str(np.round(jn.parameters.azimuth()*180/np.pi,0)) + ' degrees')
print('Expected angle of semi major axis = ' + str(np.round(linPolVals[idx])) + ' degrees')
