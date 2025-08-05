# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 11:27:39 2023

@author: Lab-user
"""
import serial
import time
from tqdm import tqdm
import pandas as pd

fullFileName = r'D:\!User files\Ben\2023\2023_06_05 Ellipticity measurements with extra ELL14\2023_06_05 Ellip measurements MAITAI.xlsx'
dfHWP = pd.read_excel(fullFileName, usecols='C')
dfQWP = pd.read_excel(fullFileName, usecols='D')

import winsound
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

def serialtoDeg(serialString): #converts hex numbers from stage into degrees
    pos = round((int(serialString.strip()[3:],16)/143360*360),2)        # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    return pos
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
time.sleep(0.2)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')
    pos0 = serialtoDeg(serialString)
    
    if pos0 > 143360:
        pos0 = 0
    print('Starting position of HWP = ' + str(pos0) + 'deg' + '\n')

ELLser.write(('2gp' + '\n').encode('utf-8'))    # Check stage position (to make sure homing worked properly)                  
time.sleep(0.2)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    pos2 = serialtoDeg(serialString)
    
    if pos2 > 143360:
        pos2 = 0
    print('Starting position of QWP = ' + str(pos2) + 'deg' + '\n')

HWPMoveArray = []
for idx in range(0,14):   
    HWPdeg = int(dfHWP.values[idx+2])    
    abMove = '0ma'+ str(degreestoHex(HWPdeg).zfill(8))
    HWPMoveArray.append(abMove)
    
time.sleep(1)

for idx in range(0,14):
    ELLser.write(HWPMoveArray[idx].encode('utf-8'))     # Move to absolute position
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
   
    

ELLser.close()
ARDser.close()

























