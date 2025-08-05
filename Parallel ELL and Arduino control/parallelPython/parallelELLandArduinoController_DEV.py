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

jogStepSize = degreestoHex(8)   #Set jog step size (in degrees) here

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

writeString = '0sj00000'+ str(jogStepSize)      # Set jog step size for first ELL14
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

abMove01 = '0ma0000'+str(degreestoHex(58))  #Define a series of absolute movements.  
abMove02 = '0ma0000'+str(degreestoHex(46))
abMove03 = '0ma0000'+str(degreestoHex(33))
abMove04 = '0ma0000'+str(degreestoHex(24))
abMove05 = '0ma0000'+str(degreestoHex(20))
abMove06 = '0ma0000'+str(degreestoHex(20))
abMove07 = '0ma0000'+str(degreestoHex(19))   
abMove08 = '0ma0000'+str(degreestoHex(16))
abMove09 = '0ma0000'+str(degreestoHex(12))
abMove10 = '0ma000'+str(degreestoHex(359))
abMove11 = '0ma000'+str(degreestoHex(350))
abMove12 = '0ma000'+str(degreestoHex(338))
abMove13 = '0ma000'+str(degreestoHex(327))   
abMove14 = '0ma000'+str(degreestoHex(316))
HWPMoveStringArray = [abMove01, abMove02, abMove03, abMove04, abMove05, abMove06,abMove07,abMove08,abMove09,abMove10,abMove11,abMove12,abMove13,abMove14]

abMove01 = '2ma0000'+str(degreestoHex(133))  #Define a series of absolute movements.  
abMove02 = '2ma0000'+str(degreestoHex(119))
abMove03 = '2ma0000'+str(degreestoHex(98))
abMove04 = '2ma0000'+str(degreestoHex(76))
abMove05 = '2ma0000'+str(degreestoHex(64))
abMove06 = '2ma0000'+str(degreestoHex(52))
abMove07 = '2ma0000'+str(degreestoHex(41))   
abMove08 = '2ma0000'+str(degreestoHex(25))
abMove09 = '2ma0000'+str(degreestoHex(12))
abMove10 = '2ma000'+str(degreestoHex(352))
abMove11 = '2ma000'+str(degreestoHex(343))
abMove12 = '2ma000'+str(degreestoHex(331))
abMove13 = '2ma000'+str(degreestoHex(321))   
abMove14 = '2ma000'+str(degreestoHex(305))
QWPMoveStringArray = [abMove01, abMove02, abMove03, abMove04, abMove05, abMove06,abMove07,abMove08,abMove09,abMove10,abMove11,abMove12,abMove13,abMove14]

print('Loop starts \n\n')
time.sleep(1)
for idx in tqdm(range(0,len(HWPMoveStringArray))):    # In each iteration, first ELL14 takes a regular sized jog step, and second moves to an impirically determined absolute position
    
   
    ELLser.write((HWPMoveStringArray[idx]).encode('utf-8'))     # Move to absolute position
    time.sleep(1.0)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')                
        pos0 = round(serialtoDeg(serialString))   
        print(' \n Current position of HWP = ' + str(pos0) + ' deg' + '\n')
    
    ELLser.write((QWPMoveStringArray[idx]).encode('utf-8'))     # Move to absolute position
    time.sleep(1.0)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')                
        pos2 = round(serialtoDeg(serialString))   
        print(' \n Current position of QWP = ' + str(pos2) + ' deg' + '\n')
        
    ARDser.write('on'.encode())     #Serial communication to Arduino - after both ELL14s have moved, turn on Arduino digital output to act as a trigger pulse for other parts of the experiment
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

    time.sleep(5.5) #IMAGE ACQUISTION occurs during this timestep before the loop iterates
ELLser.close()
ARDser.close()
            

#%%
