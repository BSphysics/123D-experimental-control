# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 15:52:16 2023

@author: bs426
"""
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
# import matplotlib.pyplot as plt
from py_pol.jones_vector import Jones_vector
# from py_pol.jones_matrix import Jones_matrix
from py_pol.utils import degrees

# plt.close('all')

def polarizationLineariser(delta):

    delta = delta * degrees # The phase retardance of the microscope components
    
    phiArr = np.arange(0,180,0.1) * degrees
    thetaArr = np.arange(0,90,0.1) * degrees
    res=[]
    
    for theta in thetaArr:
        
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

