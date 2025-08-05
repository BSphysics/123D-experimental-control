# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 10:29:43 2023

@author: Lab-user
"""
import numpy as np
import serial
import time
# from tqdm import tqdm
import matplotlib
matplotlib.use('Qt5Agg')
# import matplotlib.pyplot as plt
# from py_pol.utils import degrees

degrees = np.pi/180
serialString = ""  # declare a string variable

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


def degreestoHex(deg):          # Quick fn to convert degrees of rotation into the number of pulses needed to actuate this rotation (number in hexadecimal) 
    # first convert degrees to pulses
    pulses = int(deg/360*143360)    # # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    
    # convert pulses into hex
    hexPulses = hex(pulses).upper()  #  Hex characters have to be capitals
    return hexPulses[2:]

def serialtoDeg(serialString): #converts hex numbers from stage into degrees
    pos = round((int(serialString.strip()[3:],16)/143360*360),2)        # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    return pos
#%% Set polariser position for pSHG sequence measurement

ELLser.reset_input_buffer()
ELLser.flushInput()             # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
ELLser.flushOutput() 

ELLser.write(('1in' + '\n').encode('utf-8'))    # request information about the first ELL14
time.sleep(0.2)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')   # Serial message back from ELL14            
    print(serialString)

ELLser.write(('1ho' + '\n').encode('utf-8'))    # Home ELL14
time.sleep(2.0)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii') 
    
# polMove = '1ma0000'+str(degreestoHex(58))

polMove = '1ma'+ str(degreestoHex(315 - 0.0).zfill(8))
    
ELLser.write((polMove).encode('utf-8'))     # Move to absolute position
time.sleep(2.0)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    pos0 = round(serialtoDeg(serialString))   
    print(' \n Current position of polariser = ' + str(pos0) + ' deg' + '\n')


#%%
ELLser.close()
ARDser.close()

# import os
# from pathlib import Path
# from datetime import datetime
# today = datetime.today()
# datestamp = str(today.year)+ '_' + str(today.month)+ '_' + str(today.day)+ '_' + str(today.hour) + str(today.minute)
# saveDir = r'D:\!User files\Ben\2023\Polarisation measurements' + r'\ ' + datestamp

# data_path = Path(saveDir)
# if not os.path.exists(data_path):
#     os.mkdir(data_path)
    