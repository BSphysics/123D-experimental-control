# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 13:38:46 2023


@author: BES (b.sherlock@exeter.ac.uk)

Script controls a ELL14 (https://www.thorlabs.com/thorproduct.cfm?partnumber=ELL14) connected to the PC via USB cable -> Interface board -> ELLB bus distribution board 
The  ELL14 is at address '1' (note this is not the COM port) and all serial commands to this ELL are prefixed with a '0' e.g. '0in''


"""
import numpy as np
import serial
import time
from tqdm import tqdm
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import os
from pathlib import Path
scriptDir = os.getcwd()
import sys
sys.path.append(os.path.join(scriptDir,"functions" ))
from setConstantPolarisation import setPol
from matplotlib import patches


# calibrationFile = r'D:\!User files\Ben\2024\Polarisation testing\HWP QWP Pol angles 20 percent ellip for testing using polScan REFORMATTED.xlsx'
# calibrationFile = r'D:\!User files\Ben\2024\Polarisation testing\2024_03_13 after HWP and QWP linear pol sequence 15deg intervals REFORMATTED.xlsx'
# calibrationFile = r'D:\!User files\Ben\2024\Polarisation testing\2024_02_27 Rotating ellipse pSHG sequences\pSHG sequence for 00pc ellipticity.xlsx'
calibrationFile = r'D:\!User files\Ben\2023\2023_06_22 new pSHG sequence MIRA\2023_06_22 new pSHG sequence MIRA.xlsx' 

degrees = np.pi/180
serialString = ""  # declare a string variable

percentageEllipticity = []
polEllipseAngle = []
expectedEllipseAngles = []
Emaxs = []
Emins = []

import pandas as pd
dfHWP = pd.read_excel(calibrationFile, usecols='C')
dfQWP = pd.read_excel(calibrationFile, usecols='D')
dfLPA = pd.read_excel(calibrationFile, usecols='E')

from datetime import datetime
today = datetime.today()
datestamp = str(today.year)+ '_' + str(today.month)+ '_' + str(today.day)+ '_' + str(today.hour).zfill(2) + str(today.minute).zfill(2)
saveDir = r'D:\!User files\Ben\2024\Polarisation measurements' + r'\ ' + datestamp

data_path = Path(saveDir)
if not os.path.exists(data_path):
    os.mkdir(data_path)
    
def degreestoHex(deg):          # Quick fn to convert degrees of rotation into the number of pulses needed to actuate this rotation (number in hexadecimal) 
    # first convert degrees to pulses
    pulses = int(deg/360*143360)    # # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    
    # convert pulses into hex
    hexPulses = hex(pulses).upper()  #  Hex characters have to be capitals
    return hexPulses[2:]

def serialtoDeg(serialString): #converts hex numbers from stage into degrees
    pos = round((int(serialString.strip()[3:],16)/143360*360),2)        # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    return pos

n=14    
for polStepNumber in range(0,n):
    
    print('\n *** pSHG acquistion sequence number = ' + str(polStepNumber +1) + ' of ' + str(n) +' *** \n')
    hwp, qwp, expectedEllipseAngle = setPol(calibrationFile, polStepNumber)
    expectedEllipseAngles.append(expectedEllipseAngle)
    
    ELLser = serial.Serial(         # Open a serial connection to the ELL14. Note you can use Windows device manager to move the USB serial adapter to a different COM port if you need
        port='COM7',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )
    ELLser.reset_input_buffer()
    ELLser.flushInput()             # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
    ELLser.flushOutput()            # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
    
    
    ARDser = serial.Serial(         # Open a serial connection to the Arduino
        port='COM6',
        baudrate=9600
    )
    ARDser.reset_input_buffer()
    ARDser.flushInput()
    ARDser.flushOutput()

    
    jogStepDeg = 20
    jogStepSize = str(degreestoHex(jogStepDeg))   #Set jog step size (in degrees) here
    
    if len(jogStepSize)<4:
        jogStepSize = jogStepSize.zfill(4)
           
    ELLser.write(('1in' + '\n').encode('utf-8'))    # request information about the first ELL14
    time.sleep(0.2)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')   # Serial message back from ELL14            
        print(serialString)
    
    writeString = '1sj0000'+ str(jogStepSize)      # Set jog step size for ELL14
    ELLser.write((writeString).encode('utf-8'))                            
    time.sleep(0.2)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')                
        print(serialString)
        
    ELLser.write(("1gj" + "\n").encode('utf-8'))    # Check that jog step size has been set correctly           
    time.sleep(0.1)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')                   
        print('Jog step size = ' + str(round((int(serialString.strip()[3:],16)/143360*360),2)) + ' deg\n')
    
    
    ELLser.write(('1ho' + '\n').encode('utf-8'))    # Home ELL14
    time.sleep(1)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')                
       
       
    ELLser.write(('1gp' + "\n").encode('utf-8'))    # Check stage position (to make sure homing worked properly)       
    time.sleep(0.2)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')
        pos0 = serialtoDeg(serialString)
        
        if pos0 > 143360:
            pos0 = 0
        print('Starting position of linear polariser = ' + str(pos0) + 'deg' + '\n')
    
    print('Loop starts \n\n')
    time.sleep(1)
    powers = []
    
    polariserAngles = np.arange(0,180,jogStepDeg)
    
    for idx in tqdm(polariserAngles):    # In each iteration,  ELL14 takes a regular sized jog step
        
        ARDser.write('pol'.encode())     #Serial communication to Arduino 
        pol = ARDser.readline().decode('ascii')     #Serial communications back from the Arduino 
        print('\n Power meter = ' + str(pol.strip()) + ' V')
    
        powers.append(float(pol.strip()))
        
        ELLser.write(('1fw' + '\n').encode('utf-8'))    #Jog step
        time.sleep(0.2)
        if(ELLser.in_waiting > 0):
            serialString = ELLser.readline().decode('ascii')                
            pos0 = round(serialtoDeg(serialString))
            
            if pos0 > 143360:
                pos0 = 0
            print(' Current position of linear polariser = ' + str(pos0) + ' deg' + '\n')     
        
    
    ELLser.reset_input_buffer()
    ELLser.flushInput()             
    ELLser.flushOutput()  
    
    ARDser.reset_input_buffer()
    ARDser.flushInput()
    ARDser.flushOutput()
       
    ELLser.close()
    ARDser.close()
    #%%
    plt.close('all')
    degrees = np.pi/180
    polariserAngles = np.arange(0,180,jogStepDeg)
    fig = plt.figure(figsize = (12,6))
    ax = fig.add_subplot(121)
    plt.plot(polariserAngles,powers,'ro')
    plt.xlabel('Polariser angle (deg)')
    plt.ylabel('Laser power (V)')
    
    from scipy.optimize import curve_fit
    
    def model_f(theta,p1,p2,p3,p4):
        
      return (p1*np.cos(theta*degrees-p3))**2 + (p2*np.sin(theta*degrees-p3))**2  +p4
    
    # popt, pcov = curve_fit(model_f, polariserAngles, powers, bounds = ([0,0,0,0],[5,5,2*np.pi,0.01]))
    popt, pcov = curve_fit(model_f, polariserAngles, powers, bounds = ([0,0,0,0] , [np.max(powers)*1.5 , np.min(powers)*1.5+1e-2, 1*np.pi, 0.01]))
    
    Emax, Emin, alpha, offset = popt
    
    Emaxs.append(Emax)
    Emins.append(Emin)
    
    fittingAngles = np.arange(0,180,1)
    plt.plot(fittingAngles,model_f(fittingAngles, Emax, Emin, alpha, offset),'--b')
    plt.ylim(0,np.max(powers)*1.1)
    print('\n Ellipse semi major axis angle = ' + str(np.round(alpha*180/np.pi)) + ' degrees \n')
        
    # fig = plt.figure()
    ax = fig.add_subplot(122, aspect='auto')
    
    
    e1 = patches.Ellipse((0, 0), Emax/2, Emin/2,
                     angle = alpha*180/np.pi, linewidth=2, fill = False, zorder=1)
    
    ax.add_patch(e1)
    ax.set_xlim([-0.5,0.5])
    ax.set_ylim([-0.5,0.5])
    ax.axis('off')
    plt.suptitle('Ellipse semi major axis = ' + str(np.round(alpha*180/np.pi)) + ' deg, ' + 'Emax = ' + str(np.round(Emax,2)) + ', Emin = ' + str(np.round(Emin,2) ))
    
    print('Fitted Emax = ' + str(np.round(Emax,2)))
    print('Fitted Emin = ' + str(np.round(Emin,2)))
    
    #%% Save the data so that fitting routines can be optimised offline (also later will need to save these data for reference)
    
    foldername = '/' + str(polStepNumber).zfill(3) + ' HWP = ' + str(hwp) + '  QWP = ' + str(qwp)
    
    data_path = saveDir + foldername
    data_path = Path(data_path)
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    np.save(data_path / 'polariserAngles', polariserAngles)
    np.save(data_path / 'powers' , powers)
    
    data_path=[]
    
    data_path = saveDir + foldername
    # plt.savefig(data_path + '/HWP = ' + str(hwp) + '  QWP = ' + str(qwp) + ' fit and ellipse.png')
    plt.savefig(saveDir + '/' + str(polStepNumber) + '__HWP = ' + str(hwp).zfill(3) + '  QWP = ' + str(qwp).zfill(3) + ' fit and ellipse.png')
    
    #%%
    
    if Emax > Emin:
        a = Emax
        b = Emin
    else:
        a = Emin
        b = Emax
    
    ellip = b/a *100
    percentageEllipticity.append(np.round(ellip,2))
    
    ellipAngle = alpha*180/np.pi
    polEllipseAngle.append(ellipAngle)
#%%
plt.close('all')
plt.figure()
plt.plot(np.asarray(percentageEllipticity), 'ro')
plt.title('Percentage Ellipticity')
plt.savefig(saveDir + '/Percentage Ellipticity.png')
np.save(saveDir + '/Percentage Ellipticity', percentageEllipticity)

plt.figure()
plt.plot(polEllipseAngle - np.asarray(expectedEllipseAngles) %90, 'go')
plt.title('Difference between expected vs measured ellipse angles')
np.save(saveDir + '/alphas', polEllipseAngle)
#%%
fig, axs = plt.subplots(2,7, figsize=(30, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = .5, wspace=.1)
axs = axs.ravel()

polEllipseAngles = np.array(polEllipseAngle)-0

for idx in range(n):
    
    e1 = patches.Ellipse((0, 0), Emaxs[idx], Emins[idx],
                     angle = polEllipseAngles[idx], linewidth=2, fill = False, zorder=1)
    
    axs[idx].add_patch(e1)
    axs[idx].set_xlim([-1.5,1.5])
    axs[idx].set_ylim([-1.5,1.5])
    axs[idx].axis('off')
    axs[idx].set_title(str(np.round(polEllipseAngles[idx],1)))
plt.suptitle('pSHG polarisation electric field ellipses' + 'Sequence used:' + calibrationFile)
plt.savefig(saveDir + '/pSHG polarisation E-field ellipses.png')

#%%
fig, axs = plt.subplots(2,7, figsize=(30, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = .5, wspace=.1)
axs = axs.ravel()

polEllipseAngles = np.array(polEllipseAngle)-105

for idx in range(n):
    
    e1 = patches.Ellipse((0, 0), Emaxs[idx]**2, Emins[idx]**2,
                     angle = polEllipseAngles[idx], linewidth=2, fill = False, zorder=1)
    
    axs[idx].add_patch(e1)
    axs[idx].set_xlim([-1.5,1.5])
    axs[idx].set_ylim([-1.5,1.5])
    axs[idx].axis('off')
    axs[idx].set_title(str(np.round(polEllipseAngles[idx],1)))
plt.suptitle('pSHG polarisation intensity ellipses\n' + 'Sequence used:' + calibrationFile )
plt.savefig(saveDir + '/pSHG polarisation intensity ellipses.png')

plt.close('all')

import winsound  #Use to make a warning sound if there is a problem with the pSHG sequence 
frequency = 1000  # Set Frequency (Hz)
duration = 200  # Set Duration (mS)

winsound.Beep(int(frequency/4), int(duration*2))
winsound.Beep(int(frequency/4), int(duration*2))
print(' \n **ACQUISITION FINISHED SUCCESSFULLY**')

#%%
path = os.path.realpath(saveDir)
os.startfile(path)  