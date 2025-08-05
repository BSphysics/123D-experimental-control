# -*- coding: utf-8 -*-
"""
Created on Thu Jan  6 16:00:59 2022


@author: BES (b.sherlock@exeter.ac.uk)

Script controls a pair of Thorlabs ELL14s (https://www.thorlabs.com/thorproduct.cfm?partnumber=ELL14) connected to the PC via USB cable -> Interface board -> ELLB bus distribution board 
The first ELL14 is at address '0' (note this is not the COM port) and all serial commands to this ELL are prefixed with a '0' e.g. '0in''
The second ELL14 is at address '2' and all serial commands are prefixed with a '2' e.g. '2ho'

"""

import serial
import time
from tqdm import tqdm
import pandas as pd

fullFileName = r'D:\1_software\Experimental control software\2023_06_22 new pSHG sequence MIRA\2023_06_22 new pSHG sequence MIRA.xlsx' # Make sure this is the correct calibration file!!
dfHWP = pd.read_excel(fullFileName, usecols='C')
dfQWP = pd.read_excel(fullFileName, usecols='D')

import winsound  #Use to make a warning sound if there is a problem with the pSHG sequence 
frequency = 1000  # Set Frequency (Hz)
duration = 200  # Set Duration (mS)

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
    port='COM6',
    baudrate=9600
)
ARDser.reset_input_buffer()

def degreestoHex(deg):          # Quick fn to convert degrees of rotation into the number of pulses needed to actuate this rotation (number in hexadecimal) 
    # first convert degrees to pulses
    pulses = int(deg/360*143360)    # # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    
    # convert pulses into hex
    hexPulses = hex(pulses).upper()  #  Hex characters have to be capitals
    return hexPulses[2:]

# jogStepSize = degreestoHex(8)   #Set jog step size (in degrees) here

def serialtoDeg(serialString): #converts hex numbers from stage into degrees
    pos = round((int(serialString.strip()[3:],16)/143360*360),2)        # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    return pos

ELLser.write(('0in' + '\n').encode('utf-8'))    # request information about the first ELL14
time.sleep(0.5)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')   # Serial message back from ELL14            
    print(serialString)


ELLser.write(('2in' + '\n').encode('utf-8'))    #request information about the second ELL14
time.sleep(0.5)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    print(serialString)

ELLser.write(('0ho' + '\n').encode('utf-8'))    # Home first ELL14
time.sleep(1)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    # print(serialString)

ELLser.write(('2ho' + '\n').encode('utf-8'))    #Home second ELL14
time.sleep(1)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    # print(serialString)
    
ELLser.write(('0gp' + "\n").encode('utf-8'))    # Check stage position (to make sure homing worked properly)       
time.sleep(1)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')
    pos0 = serialtoDeg(serialString)
    
    if pos0 > 143360:
        pos0 = 0
    print('Starting position of HWP = ' + str(pos0) + ' deg' + '\n')

ELLser.write(('2gp' + '\n').encode('utf-8'))    # Check stage position (to make sure homing worked properly)                  
time.sleep(1)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    pos2 = serialtoDeg(serialString)
    
    if pos2 > 143360:
        pos2 = 0
    print('Starting position of QWP = ' + str(pos2) + ' deg' + '\n')

HWPMoveArray = []
for idx in range(0,14):   
    HWPdeg = int(dfHWP.values[idx+2])    
    abMove = '0ma'+ str(degreestoHex(HWPdeg).zfill(8))
    HWPMoveArray.append(abMove)

QWPMoveArray = []
for idx in range(0,14):   
    QWPdeg = int(dfQWP.values[idx+2])    
    QWPabMove = '2ma'+ str(degreestoHex(QWPdeg).zfill(8))
    QWPMoveArray.append(QWPabMove)
    

ELLser.flushInput()     # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
ELLser.flushOutput()    # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
    
print('Loop starts \n\n')
time.sleep(1)
for idx in tqdm(range(0,14)):    # In each iteration, first ELL14 takes a regular sized jog step, and second moves to an impirically determined absolute position
   
    ELLser.write((HWPMoveArray[idx]).encode('utf-8'))     # Move to absolute position
    time.sleep(1.0)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')                
        pos0 = round(serialtoDeg(serialString))   
        print(' \n  Target position of HWP = ' + str(round(serialtoDeg(HWPMoveArray[idx]))) + ' deg')
        print(' Current position of HWP = ' + str(pos0) + ' deg' + '\n')
        
        target = round(serialtoDeg(HWPMoveArray[idx]))
        actual = round(pos0)
        
        if target != actual:
            winsound.Beep(frequency, duration)
            winsound.Beep(frequency, duration)
            winsound.Beep(frequency, duration)
            
            print('pSHG sequence ERROR - RESTART SPYDER')
            print('pSHG sequence ERROR - RESTART SPYDER')
            print('pSHG sequence ERROR - RESTART SPYDER')
    
    ELLser.write((QWPMoveArray[idx]).encode('utf-8'))     # Move to absolute position
    time.sleep(1.0)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')                
        pos2 = round(serialtoDeg(serialString))   
        print(' \n  Target position of QWP = ' + str(round(serialtoDeg(QWPMoveArray[idx]))) + ' deg')
        print(' Current position of QWP = ' + str(pos2) + ' deg' + '\n')
        
        target = round(serialtoDeg(QWPMoveArray[idx]))
        actual = round(pos2)
        
        if target != actual:
            winsound.Beep(frequency, duration)
            winsound.Beep(frequency, duration)
            winsound.Beep(frequency, duration)
            
            print('pSHG sequence ERROR - RESTART SPYDER')
            print('pSHG sequence ERROR - RESTART SPYDER')
            print('pSHG sequence ERROR - RESTART SPYDER')
        
    ARDser.write('on'.encode())     #Serial communication to Arduino - after both ELL14s have moved, turn on Arduino digital output to act as a trigger pulse for other parts of the experiment
    time.sleep(0.2)
    led = ARDser.readline().decode('ascii')     #Serial communications back from the Arduino (not really very important)
    # print(led)
    DI02 = ARDser.readline().decode('ascii')
    # print(DI02)    
    time.sleep(0.1)
    ARDser.write('off'.encode())    # Turn off Arduino digital output (to create a TTL pulse)
    time.sleep(0.2)
    led  =ARDser.readline().decode('ascii')
    # print(led)
    DI02 = ARDser.readline().decode('ascii')
    # print(DI02) 

    time.sleep(5.5) #IMAGE ACQUISTION occurs during this timestep before the loop iterates 
  
ELLser.close()
ARDser.close()


# Beep
winsound.Beep(1000, 300)  # 1000 Hz for 300 ms
time.sleep(0.1)           # Short pause between tones
winsound.Beep(600, 300)   # 600 Hz for 300 ms

            

#%%
