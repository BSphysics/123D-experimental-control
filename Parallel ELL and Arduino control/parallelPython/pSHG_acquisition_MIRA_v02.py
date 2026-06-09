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
import sys


# fullFileName = r'D:\1_software\Experimental control software\2023_06_22 new pSHG sequence MIRA\2023_06_22 new pSHG sequence MIRA.xlsx' # Make sure this is the correct calibration file!!
# fullFileName = r'D:\1_software\Experimental control software\Synthetic birefringence\Fast axis 165\delta_waves=0.250_fast_axis=165.xlsx'
fullFileName = r'D:\1_software\Experimental control software\Synthetic birefringence\delta 0.25\delta_waves=0.250_fast_axis=165.xlsx'
# fullFileName = r'D:\1_software\Experimental control software\Synthetic birefringence\rotating_linear_pol.xlsx'

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
    timeout=0.2
)
ELLser.reset_input_buffer()
ELLser.flushInput()             # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
ELLser.flushOutput()            # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence

ARDser = serial.Serial(port='COM6', baudrate=9600, timeout=1) # Open a serial connection to the Arduino
ARDser.reset_input_buffer()

def wait_for_frame_done(timeout=10):
    """
    Blocks until Arduino sends FRAME_DONE.
    Adds timeout so you never hang forever.
    """
    start = time.time()

    while True:
        if ARDser.in_waiting > 0:
            msg = ARDser.readline().decode('ascii').strip()

            if msg == "FRAME_DONE":
                return

        if time.time() - start > timeout:
            raise TimeoutError("No FRAME_DONE received from Arduino")

        time.sleep(0.001)  # small CPU-friendly delay

def move_ell(addr, deg, timeout=3.0):

    ELLser.write(
        f"{addr}ma{degreestoHex(deg).zfill(8)}\n".encode('utf-8')
    )

    t0 = time.time()

    while time.time() - t0 < timeout:

        raw = ELLser.readline()

        if raw:
            print(raw)

        line = raw.decode('ascii', errors='ignore')

        if line.startswith(f"{addr}PO"):
            return serialtoDeg(line)

    raise TimeoutError(
        f"ELL{addr} move to {deg} did not complete"
    )
    
def degreestoHex(deg):          # Quick fn to convert degrees of rotation into the number of pulses needed to actuate this rotation (number in hexadecimal) 
    # first convert degrees to pulses
    pulses = int(deg/360*143360)    # # 143360 is number of pulses needed for 360 degrees of rotation on the ELL14
    
    # convert pulses into hex
    hexPulses = hex(pulses).upper()  #  Hex characters have to be capitals
    return hexPulses[2:]

import re

def serialtoDeg(serialString):

    m = re.search(r'([0-9A-F]{8})', serialString)

    if not m:
        raise ValueError(f"Bad ELL packet: {repr(serialString)}")

    hexpos = m.group(1)

    return round(int(hexpos,16)/143360*360,2)

ELLser.write(('0in' + '\n').encode('utf-8'))    # request information about the first ELL14
time.sleep(0.5)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')   # Serial message back from ELL14            
    print(serialString)

if serialString != '0IN0E1140051420211501016800023000\r\n':
    sys.exit("Unexpected response. Terminating script.")

ELLser.write(('2in' + '\n').encode('utf-8'))    #request information about the second ELL14
time.sleep(0.5)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    print(serialString)
    
if serialString != '2IN0E1140064920211501016800023000\r\n':
    sys.exit("Unexpected response. Terminating script.")

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

time.sleep(1)
def beep_error(msg):
    for _ in range(3):
        winsound.Beep(frequency, duration)
    print('\n'.join(['pSHG sequence ERROR - ' + msg] * 3))

POS_TOL = 1.0          # deg
REARM_DELAY = 0.4      # nominal head-start before first trigger attempt
ATTEMPT_TIMEOUT = 10  # MUST exceed one frame period (0.7 s) by a clear margin
MAX_TRIES = 4

def trigger_and_wait(idx):
    """Fire trigger; retry only if NO frame scanned (safe—dropped triggers scan nothing)."""
    for attempt in range(1, MAX_TRIES + 1):
        
        ARDser.write(b'on\n'); time.sleep(0.05); ARDser.write(b'off\n')
        try:
            wait_for_frame_done(timeout=ATTEMPT_TIMEOUT)
            return True
        except TimeoutError:
            print(f"Frame {idx+1}: trigger dropped (attempt {attempt}/{MAX_TRIES}), re-arming")
            time.sleep(REARM_DELAY)
    beep_error(f"Frame {idx+1} FAILED after {MAX_TRIES} tries")
    return False

print('Loop starts \n\n')
time.sleep(1)

ARDser.reset_input_buffer()

for idx in tqdm(range(14)):

    HWPdeg = int(dfHWP.values[idx + 2])
    QWPdeg = int(dfQWP.values[idx + 2])

    # -------------------------
    # Move HWP
    # -------------------------
    try:
        pos0 = move_ell('0', HWPdeg)

        if abs(pos0 - HWPdeg) > POS_TOL:
            beep_error(
                f'HWP at {pos0} deg, expected {HWPdeg} '
                f'(frame {idx + 1})'
            )

    except TimeoutError as e:
        beep_error(str(e))
        pos0 = None

    # -------------------------
    # Move QWP
    # -------------------------
    try:
        pos2 = move_ell('2', QWPdeg)

        if abs(pos2 - QWPdeg) > POS_TOL:
            beep_error(
                f'QWP at {pos2} deg, expected {QWPdeg} '
                f'(frame {idx + 1})'
            )

    except TimeoutError as e:
        beep_error(str(e))
        pos2 = None

    # -------------------------
    # Trigger acquisition
    # -------------------------
    time.sleep(REARM_DELAY)
    trigger_and_wait(idx)

ELLser.close()
ARDser.close()


# Beep
winsound.Beep(1000, 300)  # 1000 Hz for 300 ms
time.sleep(0.1)           # Short pause between tones
winsound.Beep(600, 300)   # 600 Hz for 300 ms

            

#%%
