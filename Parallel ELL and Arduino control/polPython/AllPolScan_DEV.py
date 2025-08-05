# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 13:38:46 2023


@author: BES (b.sherlock@exeter.ac.uk)

Script controls a ELL14 (https://www.thorlabs.com/thorproduct.cfm?partnumber=ELL14) connected to the PC via USB cable -> Interface board -> ELLB bus distribution board 

Aim: record polarisation state at back focal plane of microscope for every combination of HWP and QWP orientation

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
# from setConstantPolarisation import setPol
from matplotlib import patches

degrees = np.pi/180
serialString = ""  # declare a string variable

percentageEllipticity = []
polEllipseAngle = []
expectedEllipseAngles = []
Emaxs = []
Emins = []
alphas=[]
HWPangles = []
QWPangles = []

from datetime import datetime
today = datetime.today()
datestamp = str(today.year)+ '_' + str(today.month)+ '_' + str(today.day)+ '_' + str(today.hour).zfill(2) + str(today.minute).zfill(2)
saveDir = r'D:\!User files\Ben\2024\Polarisation measurements ' + datestamp + r'__AllPolScan data'

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

from scipy.optimize import curve_fit
    
def model_f(theta,p1,p2,p3,p4):
    
  return (p1*np.cos(theta*degrees-p3))**2 + (p2*np.sin(theta*degrees-p3))**2  + p4

#---------------------------------------------------Initialise Linear polariser communication---------------------
    
ELLLinPolser = serial.Serial(         # Open a serial connection to the ELL14. Note you can use Windows device manager to move the USB serial adapter to a different COM port if you need
        port='COM7',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )
ELLLinPolser.reset_input_buffer()
ELLLinPolser.flushInput()             # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
ELLLinPolser.flushOutput()            # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
     
jogStepDeg = 20
jogStepSize = str(degreestoHex(jogStepDeg))   #Set jog step size (in degrees) here

if len(jogStepSize)<4:
    jogStepSize = jogStepSize.zfill(4)

ELLLinPolser.write(('1in' + '\n').encode('utf-8'))    # request information about the ELL14 controlling the polariser
time.sleep(0.2)
if(ELLLinPolser.in_waiting > 0):
    serialString = ELLLinPolser.readline().decode('ascii')   # Serial message back from ELL14 controlling the polariser            
    print(serialString)

writeString = '1sj0000'+ str(jogStepSize)      # Set jog step size for ELL14 controlling the polariser
ELLLinPolser.write((writeString).encode('utf-8'))                            
time.sleep(0.2)
if(ELLLinPolser.in_waiting > 0):
    serialString = ELLLinPolser.readline().decode('ascii')                
    print(serialString)
    
ELLLinPolser.write(("1gj" + "\n").encode('utf-8'))    # Check that jog step size has been set correctly           
time.sleep(0.1)
if(ELLLinPolser.in_waiting > 0):
    serialString = ELLLinPolser.readline().decode('ascii')                   
    print('Jog step size = ' + str(round((int(serialString.strip()[3:],16)/143360*360),2)) + ' deg\n')


ELLLinPolser.write(('1ho' + '\n').encode('utf-8'))    # Home ELL14
time.sleep(1.5)
if(ELLLinPolser.in_waiting > 0):
    serialString = ELLLinPolser.readline().decode('ascii')                
   
   
ELLLinPolser.write(('1gp' + "\n").encode('utf-8'))    # Check stage position (to make sure homing worked properly)       
time.sleep(0.2)
if(ELLLinPolser.in_waiting > 0):
    serialString = ELLLinPolser.readline().decode('ascii')
    pos0 = serialtoDeg(serialString)
    
    if pos0 > 143360:
        pos0 = 0
    print('Starting position of linear polariser = ' + str(pos0) + ' deg' + '\n')
    
#---------------------------------------------------Initialise HWP and QWP ELL14 communication---------------------
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
ELLser.flushInput()             # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
ELLser.flushOutput() 

ARDser = serial.Serial(         # Open a serial connection to the Arduino
    port='COM6',
    baudrate=9600
)
ARDser.reset_input_buffer()
ARDser.flushInput()
ARDser.flushOutput()


ELLser.write(('0in' + '\n').encode('utf-8'))    # request information about the HWP ELL14
time.sleep(0.1)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')   # Serial message back from ELL14            
    print(serialString)
    
ELLser.write(('2in' + '\n').encode('utf-8'))    # request information about the QWP ELL14
time.sleep(0.1)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')   # Serial message back from QWP ELL14            
    print(serialString)
    
ELLser.write(('0ho' + '\n').encode('utf-8'))    # Home HWP ELL14
time.sleep(1.5)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    # print(serialString)

ELLser.write(('2ho' + '\n').encode('utf-8'))    #Home QWP ELL14
time.sleep(1.5)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    # print(serialString)
    
ELLser.write(('0gp' + "\n").encode('utf-8'))    # Check stage position (to make sure homing worked properly)       
time.sleep(0.1)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')
    pos0 = serialtoDeg(serialString)
    
    if pos0 > 143360:
        pos0 = 0
    print('Starting position of HWP = ' + str(pos0) + ' deg' + '\n')

ELLser.write(('2gp' + '\n').encode('utf-8'))    # Check stage position (to make sure homing worked properly)                  
time.sleep(0.1)
if(ELLser.in_waiting > 0):
    serialString = ELLser.readline().decode('ascii')                
    pos2 = serialtoDeg(serialString)
    
    if pos2 > 143360:
        pos2 = 0
    print('Starting position of QWP = ' + str(pos2) + ' deg' + '\n')  


# Create the HWP position  array here
HWPArray = np.arange(0,181,5)
HWPMoveArray=[]
for HWPangleIDX in range(0,len(HWPArray)):   
    HWPdeg = int(HWPArray[HWPangleIDX])  
    abMove = '0ma'+ str(degreestoHex(HWPdeg).zfill(8))
    HWPMoveArray.append(abMove)
    
# Create the QWP position  array here
QWPArray = np.arange(0,101,5)
QWPMoveArray=[]
for QWPangleIDX in range(0,len(QWPArray)):   
    QWPdeg = int(QWPArray[QWPangleIDX])    
    abMove = '2ma'+ str(degreestoHex(QWPdeg).zfill(8))
    QWPMoveArray.append(abMove)


polariserAngles = np.arange(0,180,jogStepDeg)
# Set the HWP position here
for HWPidx in range(0, len(HWPMoveArray)):
    ELLser.write(HWPMoveArray[HWPidx].encode('utf-8'))     # Move to absolute position
    time.sleep(1)
    if(ELLser.in_waiting > 0):
        serialString = ELLser.readline().decode('ascii')                
        pos0 = round(serialtoDeg(serialString))  
        if pos0 > 143360:
            pos0 = 0
        print(' \n  Target position of HWP = ' + str(round(serialtoDeg(HWPMoveArray[HWPidx]))) + ' deg')
        print(' Current position of HWP = ' + str(pos0) + ' deg' + '\n')
        
        HWPtarget = round(serialtoDeg(HWPMoveArray[HWPidx]))
        HWPactual = round(pos0)
        
        if HWPtarget != HWPactual:
            winsound.Beep(frequency, duration)
            winsound.Beep(frequency, duration)
            winsound.Beep(frequency, duration)
            
            print('pSHG sequence ERROR - RESTART SPYDER')
            print('pSHG sequence ERROR - RESTART SPYDER')
            print('pSHG sequence ERROR - RESTART SPYDER')
    
    time.sleep(0.5)
    
    # Set the QWP position here
    for QWPidx in range(0,len(QWPMoveArray)):
        ELLser.write(QWPMoveArray[QWPidx].encode('utf-8'))     # Move to absolute position
        time.sleep(1)
        if(ELLser.in_waiting > 0):
            serialString = ELLser.readline().decode('ascii')                
            pos2 = round(serialtoDeg(serialString)) 
            if pos2 > 143360:
                pos2 = 0
                           
            print(' \n  Target position of QWP = ' + str(round(serialtoDeg(QWPMoveArray[QWPidx]))) + ' deg')
            print(' Current position of QWP = ' + str(pos2) + ' deg' + '\n')
            
            QWPtarget = round(serialtoDeg(QWPMoveArray[QWPidx]))
            QWPactual = round(pos2)
            
            if QWPtarget != QWPactual:
                winsound.Beep(frequency, duration)
                winsound.Beep(frequency, duration)
                winsound.Beep(frequency, duration)
                
                print('Waveplate sequence ERROR - RESTART SPYDER')
                print('Waveplate sequence ERROR - RESTART SPYDER')
                print('Waveplate sequence ERROR - RESTART SPYDER')
        
        #---------------------Scan linear polariser here
        
        print('Polariser loop starts \n\n')
        ELLLinPolser.write(('1ho' + '\n').encode('utf-8'))    # Home ELL14
        time.sleep(1.5)
        if(ELLLinPolser.in_waiting > 0):
            serialString = ELLLinPolser.readline().decode('ascii')                
           
           
        ELLLinPolser.write(('1gp' + "\n").encode('utf-8'))    # Check stage position (to make sure homing worked properly)       
        time.sleep(0.2)
        if(ELLLinPolser.in_waiting > 0):
            serialString = ELLLinPolser.readline().decode('ascii')
            pos0 = serialtoDeg(serialString)
            
            if pos0 > 143360:
                pos0 = 0
            print('Starting position of linear polariser = ' + str(pos0) + ' deg' + '\n')
            
        # time.sleep(1)
        powers = []
        
        polariserAngles = np.arange(0,181,jogStepDeg)
        
        for idx in tqdm(polariserAngles):    # In each iteration,  ELL14 takes a regular sized jog step
            
            ARDser.write('pol'.encode())     #Serial communication to Arduino 
            pol = ARDser.readline().decode('ascii')     #Serial communications back from the Arduino 
            print('\n Power meter = ' + str(pol.strip()) + ' V')
        
            powers.append(float(pol.strip()))
            
            ELLLinPolser.write(('1fw' + '\n').encode('utf-8'))    #Jog step
            time.sleep(0.2)
            if(ELLLinPolser.in_waiting > 0):
                serialString = ELLLinPolser.readline().decode('ascii')                
                pos0 = round(serialtoDeg(serialString))
                
                if pos0 > 143360:
                    pos0 = 0
                print(' Current position of linear polariser = ' + str(pos0) + ' deg' + '\n')  
        
                
        np.save(saveDir + '/HWP = ' + str(np.round(HWPactual,1)).zfill(3) + '  QWP = ' + str(np.round(pos2)).zfill(3), [polariserAngles, powers])
        # popt, pcov = curve_fit(model_f, polariserAngles, powers, bounds = ([0,0,0,0],[5,5,2*np.pi,0.01]))
        # popt, pcov = curve_fit(model_f, polariserAngles, powers, bounds = ([0,0,0,0] , [np.max(powers)*1.5 , np.min(powers)*1.5, 1*np.pi, 0.01]))
        # Emax, Emin, alpha, offset = popt
        
        # if Emax > Emin:
        #     a = Emax
        #     b = Emin
        # else:
        #     a = Emin
        #     b = Emax
        
        # ellip = b/a *100
        # percentageEllipticity.append(np.round(ellip,2))
        
        # ellipAngle = alpha*180/np.pi
        # polEllipseAngle.append(ellipAngle)
        
        # HWPangles.append(HWPactual)
        # QWPangles.append(QWPactual)
        # Emaxs.append(Emax)
        # Emins.append(Emin)
        # alphas.append(alpha)
        
        # plt.close('all')
        # degrees = np.pi/180
   
        # fig = plt.figure(figsize = (12,6))
        # ax = fig.add_subplot(121)
        # plt.plot(polariserAngles,powers,'ro')
        # plt.xlabel('Polariser angle (deg)')
        # plt.ylabel('Laser power (V)')
        
        # fittingAngles = np.arange(0,180,1)
        # plt.plot(fittingAngles,model_f(fittingAngles, Emax, Emin, alpha, offset),'--b')
        # ax = fig.add_subplot(122, aspect='auto')
        
        
        # e1 = patches.Ellipse((0, 0), Emax/2, Emin/2,
        #                  angle = alpha*180/np.pi, linewidth=2, fill = False, zorder=1)
        
        # ax.add_patch(e1)
        # ax.set_xlim([-0.5,0.5])
        # ax.set_ylim([-0.5,0.5])
        # ax.axis('off')
        # plt.suptitle('Ellipse semi major axis = ' + str(np.round(alpha*180/np.pi)) + ' deg, ' + 'Emax = ' + str(np.round(Emax,2)) + ', Emin = ' + str(np.round(Emin,2) ))
       
        # # data_path = saveDir + foldername
        # plt.savefig(saveDir + '/HWP = ' + str(np.round(HWPactual,1)).zfill(3) + '  QWP = ' + str(np.round(pos2)).zfill(3) + ' fit and ellipse.png')
    
np.save(saveDir + '/HWPAngles', HWPangles)
np.save(saveDir + '/QWPAngles', QWPangles)
# np.save(saveDir + '/Emaxs', Emaxs)
# np.save(saveDir + '/Emins', Emins)
# np.save(saveDir + '/alphas', alphas)
# np.save(saveDir + '/percentageEllipticity', percentageEllipticity)

ELLLinPolser.reset_input_buffer()
ELLLinPolser.flushInput()             
ELLLinPolser.flushOutput()  

ARDser.reset_input_buffer()
ARDser.flushInput()
ARDser.flushOutput()
   
ELLLinPolser.close()
ARDser.close()

#--------------
    
ELLser.reset_input_buffer()
ELLser.flushInput()             # Adding these flushes massively helped with the Serial port sending the wrong values and messing up the whole sequence
ELLser.flushOutput() 
ELLser.close()

