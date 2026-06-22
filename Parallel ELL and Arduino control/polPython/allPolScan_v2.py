# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 13:38:46 2023
Hardened for the FrameSync Arduino firmware, June 2026

@author: BES (b.sherlock@exeter.ac.uk)

Records the polarisation state at the back focal plane of the microscope for
every combination of HWP and QWP orientation.  Used for calibrating the
synthetic birefringence sequences.

Controls:
  ELLLinPolser  COM8  ELL14 address '1'  linear analyser
  ELLser        COM5  ELL14 address '0'  HWP
                      ELL14 address '2'  QWP
  ARDser        COM6  Arduino (FrameSync sketch)

------------------------------------------------------------------------------
CHANGES VS ORIGINAL
------------------------------------------------------------------------------
  1. ARDser opened with timeout=1.  Without a timeout, readline() blocks
     forever when the FrameSync sketch has no 'pol' handler and returns
     nothing.

  2. wait_for_arduino_ready() called once, after the ELLLinPolser + ELLser
     init blocks.  Those take ~4-5 s total, which is well past the Arduino
     boot time, but we drain the banner explicitly to be safe.

     Unlike the previous script, ARDser stays open for the whole run, so
     wait_for_arduino_ready() is only needed once here.

  3. read_power() replaces the bare:
         ARDser.write('pol'.encode())
         pol = ARDser.readline().decode('ascii')
         powers.append(float(pol.strip()))
     Same rationale as the other scripts: the FrameSync sketch has no 'pol'
     handler and the bare pattern crashes on any non-numeric reply.

  To restore real readings, add this to the Arduino sketch's serial handler:

      if (InBytes == "pol") {
        int raw = analogRead(A0);
        float volts = raw * (5.0 / 1023.0);
        Serial.println(volts, 4);
      }
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
import sys
from scipy.optimize import curve_fit
from matplotlib import patches
from datetime import datetime
import winsound

scriptDir = os.getcwd()
sys.path.append(os.path.join(scriptDir, "functions"))

degrees = np.pi / 180
serialString = ""

percentageEllipticity = []
polEllipseAngle = []
expectedEllipseAngles = []
Emaxs = []
Emins = []
alphas = []
HWPangles = []
QWPangles = []

frequency = 1000  # Hz
duration  = 200   # ms

# =============================================================================
# SAVE-FOLDER SETUP
# =============================================================================
today = datetime.today()

date_folder = (
    f"Polarisation measurements "
    f"{today.year}_{today.month:02d}_{today.day:02d}"
)
time_folder = (
    f"{today.hour:02d}{today.minute:02d}"
    f"__AllPolScan data"
)

base_dir   = Path(r"D:\2_user_data\Ben")
daily_path = base_dir / date_folder
daily_path.mkdir(parents=True, exist_ok=True)
data_path  = daily_path / time_folder
data_path.mkdir(exist_ok=True)
saveDir    = str(data_path)


# =============================================================================
# HELPERS
# =============================================================================
def degreestoHex(deg):
    pulses    = int(deg / 360 * 143360)
    hexPulses = hex(pulses).upper()
    return hexPulses[2:]


def serialtoDeg(serialString):
    pos = round((int(serialString.strip()[3:], 16) / 143360 * 360), 2)
    return pos


def model_f(theta, p1, p2, p3, p4):
    return (p1 * np.cos(theta * degrees - p3))**2 + (p2 * np.sin(theta * degrees - p3))**2 + p4


def wait_for_arduino_ready(ser, timeout=3.0):
    """Swallow the boot banner that the Arduino prints after a port-open reset.

    ARDser stays open for the whole run here, so this is only called once
    after the ELL14 init blocks.
    """
    t0 = time.time()
    while time.time() - t0 < timeout:
        raw = ser.readline()
        if raw:
            line = raw.decode('ascii', errors='ignore').strip()
            if line.startswith('FW:'):
                print('Arduino ready: ' + line)
                break
    ser.reset_input_buffer()


def read_power(ser, timeout=2.0, attempts=3):
    """Ask the Arduino for a power-meter reading and return it as a float.

    Sends 'pol\\n' and reads replies until one parses as a number, skipping
    status/banner lines.  Raises a clear RuntimeError if the board stays
    silent (which happens when the FrameSync sketch has no 'pol' handler).
    """
    for attempt in range(1, attempts + 1):
        ser.reset_input_buffer()
        ser.write(b'pol\n')
        t0 = time.time()
        while time.time() - t0 < timeout:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode('ascii', errors='ignore').strip()
            if line == '':
                continue
            try:
                return float(line)
            except ValueError:
                print(f"   (ignored non-numeric reply: {line!r})")
                continue
        print(f"   no numeric reply to 'pol' (attempt {attempt}/{attempts})")
    raise RuntimeError(
        "Arduino never returned a numeric power reading.  The FrameSync sketch "
        "has no 'pol' handler, so there is nothing to measure the power meter "
        "with.  Add the 'pol' -> analogRead -> Serial.println(volts) block back "
        "into the firmware (see the note at the top of this file)."
    )


# =============================================================================
# INITIALISE LINEAR POLARISER (ELLLinPolser, COM8, address '1')
# =============================================================================
ELLLinPolser = serial.Serial(
    port='COM8',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=0.2,
)
ELLLinPolser.reset_input_buffer()
ELLLinPolser.flushInput()
ELLLinPolser.flushOutput()

jogStepDeg  = 20
jogStepSize = str(degreestoHex(jogStepDeg))
if len(jogStepSize) < 4:
    jogStepSize = jogStepSize.zfill(4)

ELLLinPolser.write(('1in' + '\n').encode('utf-8'))
time.sleep(0.2)
if ELLLinPolser.in_waiting > 0:
    serialString = ELLLinPolser.readline().decode('ascii')
    print(serialString)

writeString = '1sj0000' + str(jogStepSize)
ELLLinPolser.write((writeString).encode('utf-8'))
time.sleep(0.2)
if ELLLinPolser.in_waiting > 0:
    serialString = ELLLinPolser.readline().decode('ascii')
    print(serialString)

ELLLinPolser.write(("1gj" + "\n").encode('utf-8'))
time.sleep(0.1)
if ELLLinPolser.in_waiting > 0:
    serialString = ELLLinPolser.readline().decode('ascii')
    print('Jog step size = ' + str(round((int(serialString.strip()[3:], 16) / 143360 * 360), 2)) + ' deg\n')

ELLLinPolser.write(('1ho' + '\n').encode('utf-8'))
time.sleep(1.5)
if ELLLinPolser.in_waiting > 0:
    ELLLinPolser.readline()

ELLLinPolser.write(('1gp' + "\n").encode('utf-8'))
time.sleep(0.2)
if ELLLinPolser.in_waiting > 0:
    serialString = ELLLinPolser.readline().decode('ascii')
    pos0 = serialtoDeg(serialString)
    if pos0 > 143360:
        pos0 = 0
    print('Starting position of linear polariser = ' + str(pos0) + ' deg\n')


# =============================================================================
# INITIALISE HWP + QWP (ELLser, COM5, addresses '0' and '2')
# =============================================================================
ELLser = serial.Serial(
    port='COM5',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=0.2,
)
ELLser.reset_input_buffer()
ELLser.flushInput()
ELLser.flushOutput()

ELLser.write(('0in' + '\n').encode('utf-8'))
time.sleep(0.1)
if ELLser.in_waiting > 0:
    print(ELLser.readline().decode('ascii'))

ELLser.write(('2in' + '\n').encode('utf-8'))
time.sleep(0.1)
if ELLser.in_waiting > 0:
    print(ELLser.readline().decode('ascii'))

ELLser.write(('0ho' + '\n').encode('utf-8'))
time.sleep(1.5)
if ELLser.in_waiting > 0:
    ELLser.readline()

ELLser.write(('2ho' + '\n').encode('utf-8'))
time.sleep(1.5)
if ELLser.in_waiting > 0:
    ELLser.readline()

ELLser.write(('0gp' + "\n").encode('utf-8'))
time.sleep(0.1)
if ELLser.in_waiting > 0:
    serialString = ELLser.readline().decode('ascii')
    pos0 = serialtoDeg(serialString)
    if pos0 > 143360:
        pos0 = 0
    print('Starting position of HWP = ' + str(pos0) + ' deg\n')

ELLser.write(('2gp' + '\n').encode('utf-8'))
time.sleep(0.1)
if ELLser.in_waiting > 0:
    serialString = ELLser.readline().decode('ascii')
    pos2 = serialtoDeg(serialString)
    if pos2 > 143360:
        pos2 = 0
    print('Starting position of QWP = ' + str(pos2) + ' deg\n')


# =============================================================================
# INITIALISE ARDUINO (COM6) — opened once, stays open for the whole run
# =============================================================================
# timeout=1 is essential: without it, readline() blocks forever when the
# FrameSync sketch has no 'pol' handler and returns nothing.
ARDser = serial.Serial(port='COM6', baudrate=9600, timeout=1)
ARDser.reset_input_buffer()
ARDser.flushInput()
ARDser.flushOutput()

# The ELL14 init blocks above took ~4-5 s, so the Arduino has long finished
# booting, but drain any remaining banner lines to be safe.
wait_for_arduino_ready(ARDser)


# =============================================================================
# BUILD MOVE ARRAYS
# =============================================================================
HWPArray     = np.arange(0, 181, 5)
HWPMoveArray = ['0ma' + str(degreestoHex(int(a)).zfill(8)) for a in HWPArray]

QWPArray     = np.arange(0, 141, 5)
QWPMoveArray = ['2ma' + str(degreestoHex(int(a)).zfill(8)) for a in QWPArray]

polariserAngles = np.arange(0, 181, jogStepDeg)


# =============================================================================
# MAIN SCAN LOOP
# =============================================================================
for HWPidx in range(len(HWPMoveArray)):

    ELLser.write(HWPMoveArray[HWPidx].encode('utf-8'))
    time.sleep(1)
    if ELLser.in_waiting > 0:
        serialString = ELLser.readline().decode('ascii')
        pos0 = round(serialtoDeg(serialString))
        if pos0 > 143360:
            pos0 = 0
        print('\n  Target position of HWP = ' + str(round(serialtoDeg(HWPMoveArray[HWPidx]))) + ' deg')
        print(' Current position of HWP = ' + str(pos0) + ' deg\n')

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

    for QWPidx in range(len(QWPMoveArray)):

        ELLser.write(QWPMoveArray[QWPidx].encode('utf-8'))
        time.sleep(1)
        if ELLser.in_waiting > 0:
            serialString = ELLser.readline().decode('ascii')
            pos2 = round(serialtoDeg(serialString))
            if pos2 > 143360:
                pos2 = 0
            print('\n  Target position of QWP = ' + str(round(serialtoDeg(QWPMoveArray[QWPidx]))) + ' deg')
            print(' Current position of QWP = ' + str(pos2) + ' deg\n')

            QWPtarget = round(serialtoDeg(QWPMoveArray[QWPidx]))
            QWPactual = round(pos2)

            if QWPtarget != QWPactual:
                winsound.Beep(frequency, duration)
                winsound.Beep(frequency, duration)
                winsound.Beep(frequency, duration)
                print('Waveplate sequence ERROR - RESTART SPYDER')
                print('Waveplate sequence ERROR - RESTART SPYDER')
                print('Waveplate sequence ERROR - RESTART SPYDER')

        # -----------------------------------------------------------------
        # HOME AND CONFIRM LINEAR ANALYSER
        # -----------------------------------------------------------------
        print('Polariser loop starts \n\n')
        ELLLinPolser.write(('1ho' + '\n').encode('utf-8'))
        time.sleep(1.5)
        if ELLLinPolser.in_waiting > 0:
            ELLLinPolser.readline()

        ELLLinPolser.write(('1gp' + "\n").encode('utf-8'))
        time.sleep(0.2)
        if ELLLinPolser.in_waiting > 0:
            serialString = ELLLinPolser.readline().decode('ascii')
            pos0 = serialtoDeg(serialString)
            if pos0 > 143360:
                pos0 = 0
            print('Starting position of linear polariser = ' + str(pos0) + ' deg\n')

        # -----------------------------------------------------------------
        # ANALYSER ROTATION LOOP
        # -----------------------------------------------------------------
        powers = []

        for idx in tqdm(polariserAngles):
            time.sleep(0.5)
            pol = read_power(ARDser)                    # <-- robust power read
            print('\n Power meter = ' + str(pol) + ' V')
            powers.append(pol)

            ELLLinPolser.write(('1fw' + '\n').encode('utf-8'))
            time.sleep(0.2)
            if ELLLinPolser.in_waiting > 0:
                serialString = ELLLinPolser.readline().decode('ascii')
                pos0 = round(serialtoDeg(serialString))
                if pos0 > 143360:
                    pos0 = 0
                print(' Current position of linear polariser = ' + str(pos0) + ' deg\n')

        # -----------------------------------------------------------------
        # FIT
        # -----------------------------------------------------------------
        popt, pcov = curve_fit(
            model_f, polariserAngles, powers,
            bounds=([0, 0, 0, 0], [np.max(powers) * 1.5, np.min(powers) * 1.5 + 1e-2, 1 * np.pi, 0.01]))
        Emax, Emin, alpha, offset = popt

        if Emax > Emin:
            a, b = Emax, Emin
        else:
            a, b = Emin, Emax

        ellip = b / a * 100
        percentageEllipticity.append(np.round(ellip, 2))
        polEllipseAngle.append(alpha * 180 / np.pi)
        HWPangles.append(HWPactual)
        QWPangles.append(QWPactual)
        Emaxs.append(Emax)
        Emins.append(Emin)
        alphas.append(alpha)

        # -----------------------------------------------------------------
        # PLOT AND SAVE
        # -----------------------------------------------------------------
        plt.close('all')
        fig = plt.figure(figsize=(12, 6))
        ax = fig.add_subplot(121)
        plt.plot(polariserAngles, powers, 'ro')
        plt.xlabel('Polariser angle (deg)')
        plt.ylabel('Laser power (V)')

        fittingAngles = np.arange(0, 180, 1)
        plt.plot(fittingAngles, model_f(fittingAngles, Emax, Emin, alpha, offset), '--b')
        plt.ylim(0, np.max(powers) * 1.1)

        ax = fig.add_subplot(122, aspect='auto')
        e1 = patches.Ellipse((0, 0), Emax / 2, Emin / 2,
                              angle=alpha * 180 / np.pi, linewidth=2, fill=False, zorder=1)
        ax.add_patch(e1)
        ax.set_xlim([-0.5, 0.5])
        ax.set_ylim([-0.5, 0.5])
        ax.axis('off')
        plt.suptitle('Ellipse semi major axis = ' + str(np.round(alpha * 180 / np.pi)) + ' deg, '
                     + 'Emax = ' + str(np.round(Emax, 2)) + ', Emin = ' + str(np.round(Emin, 2)))

        plt.savefig(saveDir + '/HWP = ' + str(np.round(HWPactual, 1)).zfill(3)
                    + '  QWP = ' + str(np.round(pos2)).zfill(3) + ' fit and ellipse.png')


# =============================================================================
# SAVE ALL RESULTS
# =============================================================================
np.save(saveDir + '/HWPAngles',            HWPangles)
np.save(saveDir + '/QWPAngles',            QWPangles)
np.save(saveDir + '/Emaxs',               Emaxs)
np.save(saveDir + '/Emins',               Emins)
np.save(saveDir + '/alphas',              alphas)
np.save(saveDir + '/percentageEllipticity', percentageEllipticity)

# =============================================================================
# CLOSE ALL PORTS
# =============================================================================
for ser in (ELLLinPolser, ARDser):
    ser.reset_input_buffer()
    ser.flushInput()
    ser.flushOutput()
    ser.close()

ELLser.reset_input_buffer()
ELLser.flushInput()
ELLser.flushOutput()
ELLser.close()

winsound.Beep(int(frequency / 4), int(duration * 2))
winsound.Beep(int(frequency / 4), int(duration * 2))
print('\n **ACQUISITION FINISHED SUCCESSFULLY**')

path = os.path.realpath(saveDir)
os.startfile(path)
