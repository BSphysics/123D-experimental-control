# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 13:38:46 2023


@author: BES (b.sherlock@exeter.ac.uk)

Script controls a ELL14 (https://www.thorlabs.com/thorproduct.cfm?partnumber=ELL14) connected to the PC via USB cable -> Interface board -> ELLB bus distribution board 
The  ELL14 is at address '0' (note this is not the COM port) and all serial commands to this ELL are prefixed with a '0' e.g. '0in''


"""
import numpy as np
import serial
import time
from tqdm import tqdm
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from py_pol.utils import degrees

serialString = ""  # declare a string variable

ELLser = serial.Serial(         # Open a serial connection to the ELL14. Note you can use Windows device manager to move the USB serial adapter to a different COM port if you need
    port='COM5',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)
ELLser.reset_input_buffer()
ELLser.flushInput()             # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
ELLser.flushOutput()            # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence


ARDser = serial.Serial(         # Open a serial connection to the Arduino
    port='COM4',
    baudrate=9600
)
ARDser.reset_input_buffer()
ARDser.flushInput()
ARDser.flushOutput()


def degreestoHex(deg):          # Quick fn to convert degrees of rotation into the number of pulses needed to actuate this rotation (number in hexadecimal) 
    # first convert degrees to pulses
    pulses = int(deg/360*143360)    # # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    
    # convert pulses into hex
    hexPulses = hex(pulses).upper()  #  Hex characters have to be capitals
    return hexPulses[2:]

jogStepDeg = 20
jogStepSize = str(degreestoHex(jogStepDeg))   #Set jog step size (in degrees) here

if len(jogStepSize)<4:
    jogStepSize = jogStepSize.zfill(4)
    
def serialtoDeg(serialString): #converts hex numbers from stage into degrees
    pos = round((int(serialString.strip()[3:],16)/143360*360),2)        # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    return pos

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
    time.sleep(0.1)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')                
        pos0 = round(serialtoDeg(serialString))
        
        if pos0 > 143360:
            pos0 = 0
        print(' Current position of linear polariser = ' + str(pos0) + ' deg' + '\n')     
    

    
ELLser.close()
ARDser.close()
            #%%
polariserAngles = np.arange(0,180,20)
plt.figure()
plt.plot(polariserAngles,powers,'ro')

from scipy.optimize import curve_fit

def model_f(theta,p1,p2,p3):
    
  return (p1*np.cos(theta*degrees-p3))**2 + (p2*np.sin(theta*degrees-p3))**2

popt, pcov = curve_fit(model_f, polariserAngles, powers, p0=[0,0,0])

Ex, Ey, alpha = popt
fittingAngles = np.arange(0,180,1)

plt.plot(fittingAngles,model_f(fittingAngles, Ex, Ey, alpha),'--b')

print('\n Ellipse semi major axis angle = ' + str(np.round(alpha*degrees)) + ' degrees')

#%%
from matplotlib import patches
fig = plt.figure()
ax = fig.add_subplot(211, aspect='auto')


e1 = patches.Ellipse((0, 0), Ex, Ey,
                 angle = alpha*degrees, linewidth=2, fill = False, zorder=1)

ax.add_patch(e1)
ax.axis('square')
ax.axis('off')
plt.title('Polarisation ellipse')