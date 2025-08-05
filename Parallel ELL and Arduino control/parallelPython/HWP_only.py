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

serialString = ""  # declare a string variable

ELLser = serial.Serial(         # Open a serial connection to the ELL14. Note you can use Windows device manager to move the USB serial adapter to a different COM port if you need
    port='COM4',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)
ELLser.reset_input_buffer()

ARDser = serial.Serial(         # Open a serial connection to the Arduino
    port='COM5',
    baudrate=9600
)
ARDser.reset_input_buffer()

def degreestoHex(deg):          # Quick fn to convert degrees of rotation into the number of pulses needed to actuate this rotation (number in hexadecimal) 
    # first convert degrees to pulses
    pulses = int(deg/360*143360)    # # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    
    # convert pulses into hex
    hexPulses = hex(pulses).upper()  #  Hex characters have to be capitals
    return hexPulses[2:]

jogStepSize = str(degreestoHex(8))   #Set jog step size (in degrees) here

if len(jogStepSize)<4:
    jogStepSize = jogStepSize.zfill(4)
    
def serialtoDeg(serialString): #converts hex numbers from stage into degrees
    pos = round((int(serialString.strip()[3:],16)/143360*360),2)        # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    return pos

ELLser.write(('0in' + '\n').encode('utf-8'))    # request information about the first ELL14
time.sleep(0.5)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')   # Serial message back from ELL14            
    print(serialString)

writeString = '0sj0000'+ str(jogStepSize)      # Set jog step size for ELL14
ELLser.write((writeString).encode('utf-8'))                            
time.sleep(0.5)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    print(serialString)
    
ELLser.write(("0gj" + "\n").encode('utf-8'))    # Check that jog step size has been set correctly           
time.sleep(0.1)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                   
    print('Jog step size = ' + str(round((int(serialString.strip()[3:],16)/143360*360),2)) + ' deg')


ELLser.write(('0ho' + '\n').encode('utf-8'))    # Home ELL14
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

print('Loop starts \n\n')
time.sleep(1)
for idx in tqdm(range(0,14)):    # In each iteration,  ELL14 takes a regular sized jog step
    
    ELLser.write(('0fw' + '\n').encode('utf-8'))    #Jog step
    time.sleep(1.0)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')                
        pos0 = round(serialtoDeg(serialString))
        
        if pos0 > 143360:
            pos0 = 0
        print('\n Current position of HWP = ' + str(pos0) + ' deg' + '\n') 
        print('\n Hi JR! \n')


        
    ARDser.write('on'.encode())     #Serial communication to Arduino - after ELL14 has moved, turn on Arduino digital output to act as a trigger pulse for other parts of the experiment
    time.sleep(0.2)
    led = ARDser.readline().decode('ascii')     #Serial communications back from the Arduino (not really very important)
    # print(led)
    DI02 = ARDser.readline().decode('ascii')
    # print(DI02)    

    ARDser.write('off'.encode())    # Turn off Arduino digital output (to create a TTL pulse)
    time.sleep(0.2)
    led  =ARDser.readline().decode('ascii')
    # print(led)
    DI02 = ARDser.readline().decode('ascii')
    # print(DI02) 

    time.sleep(1.5) #IMAGE ACQUISTION occurs during this timestep before the loop iterates
ELLser.close()
ARDser.close()
            
