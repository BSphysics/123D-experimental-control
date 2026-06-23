# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 13:38:46 2023
Hardened for the FrameSync Arduino firmware, June 2026

@author: BES (b.sherlock@exeter.ac.uk)

Multi-step polarisation scan: iterates over n HWP/QWP positions from a
calibration file, at each step rotating a linear analyser (ELL14 on COM8)
through 0-180 deg and reading the power meter from an Arduino on COM6.

------------------------------------------------------------------------------
CHANGES VS ORIGINAL (same rationale as ellipMeasure_v2.py)
------------------------------------------------------------------------------
  1. ARDser opened with timeout=1 (was no timeout -> readline() blocked forever).

  2. wait_for_arduino_ready() added.  The Arduino resets when COM6 is opened,
     printing a boot banner ("FW:FrameSync_INT_v1_READY") a beat AFTER
     reset_input_buffer() runs.  Calling this after each ARDser open() swallows
     that banner so it is never mistaken for a power value.
     Because the ELL14 setup block takes ~1-2 s on each loop iteration, the
     Arduino has usually finished booting by the time we call it -- but we
     call it explicitly to be safe.

  3. read_power() replaces the bare:
         ARDser.write('pol'.encode())
         pol = ARDser.readline().decode('ascii')
         powers.append(float(pol.strip()))
     That pattern crashes if the FrameSync sketch returns a status line or
     nothing at all (it has no 'pol' handler by default).  read_power()
     retries, skips non-numeric lines, and raises a clear error if the board
     stays silent.

  To restore real readings, add this to the Arduino sketch's serial handler
  (it sits alongside on/off/ping without disturbing the frame ISR):

      if (InBytes == "pol") {
        int raw = analogRead(A0);            // <-- your power-meter input pin
        float volts = raw * (5.0 / 1023.0);  // <-- match your old scaling/AREF
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
scriptDir = os.getcwd()
import sys
sys.path.append(os.path.join(scriptDir, "functions"))
from setConstantPolarisation import setPol
from matplotlib import patches
from scipy.optimize import curve_fit
from datetime import datetime

calibrationFile = r'D:\1_software\Experimental control software\2023_06_22 new pSHG sequence MIRA\2023_06_22 new pSHG sequence MIRA.xlsx'
# calibrationFile = r'D:\1_software\Experimental control software\Synthetic birefringence\0pt25 waves\delta_waves=0.250_fast_axis=70.xlsx'

degrees = np.pi / 180
serialString = ""

percentageEllipticity = []
polEllipseAngle = []
expectedEllipseAngles = []
Emaxs = []
Emins = []
fitParams = []   # [Emax, Emin, alpha, offset] per step
fitCovs   = []   # full 4x4 covariance per step
rawScans  = []   # (polariserAngles, powers) per step, for offline refitting

import pandas as pd
dfHWP = pd.read_excel(calibrationFile, usecols='C')
dfQWP = pd.read_excel(calibrationFile, usecols='D')
dfLPA = pd.read_excel(calibrationFile, usecols='E')

today = datetime.today()

date_folder = (
    f"Polarisation measurements "
    f"{today.year}_{today.month:02d}_{today.day:02d}"
)
time_folder = (
    f"{today.hour:02d}{today.minute:02d}"
    f"__PolScan data" + " using " + os.path.splitext(os.path.basename(calibrationFile))[0]
)

base_dir = Path(r"D:\2_user_data\Ben")

daily_path = base_dir / date_folder
daily_path.mkdir(parents=True, exist_ok=True)

data_path = daily_path / time_folder
data_path.mkdir(exist_ok=True)

saveDir = str(data_path)

data_path = Path(saveDir)
if not os.path.exists(data_path):
    os.mkdir(data_path)


# =============================================================================
# HELPERS
# =============================================================================
def degreestoHex(deg):
    pulses = int(deg / 360 * 143360)
    hexPulses = hex(pulses).upper()
    return hexPulses[2:]


def serialtoDeg(serialString):
    pos = round((int(serialString.strip()[3:], 16) / 143360 * 360), 2)
    return pos


def wait_for_arduino_ready(ser, timeout=3.0):
    """Opening the port resets the Arduino; swallow its boot banner so it
    doesn't get read as the first power value.

    Takes the serial object as an argument because in this script the port is
    opened and closed on every loop iteration.
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

    Takes the serial object as an argument because in this script the port is
    opened and closed on every loop iteration.

    Sends 'pol\\n' and reads replies until one parses as a number, skipping
    status/banner lines.  If the board never returns a number, raises a clear
    error naming the likely cause.
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
        "Arduino never returned a numeric power reading. The FrameSync sketch "
        "has no 'pol' handler, so there is nothing to measure the power meter "
        "with. Add the 'pol' -> analogRead -> Serial.println(volts) block back "
        "into the firmware (see the note at the top of this file)."
    )


# =============================================================================
# MAIN LOOP
# =============================================================================
jogStepDeg = 20
jogStepSize = str(degreestoHex(jogStepDeg))
if len(jogStepSize) < 4:
    jogStepSize = jogStepSize.zfill(4)

n = 14
for polStepNumber in range(0, n):

    print('\n *** pSHG acquisition sequence number = ' + str(polStepNumber + 1) + ' of ' + str(n) + ' *** \n')
    hwp, qwp, expectedEllipseAngle = setPol(calibrationFile, polStepNumber)
    expectedEllipseAngles.append(expectedEllipseAngle)

    ELLser = serial.Serial(
        port='COM8',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.2,          # prevents reads blocking if the stage is quiet
    )
    ELLser.reset_input_buffer()
    ELLser.flushInput()
    ELLser.flushOutput()

    # timeout=1 is essential: without it readline() blocks forever when the
    # FrameSync sketch returns nothing (e.g. for an unrecognised command).
    ARDser = serial.Serial(port='COM6', baudrate=9600, timeout=1)
    ARDser.reset_input_buffer()
    ARDser.flushInput()
    ARDser.flushOutput()

    # --- ELL14 setup (takes ~1-2 s, giving the Arduino time to finish booting) ---
    ELLser.write(('1in' + '\n').encode('utf-8'))
    time.sleep(0.2)
    if ELLser.in_waiting > 0:
        serialString = ELLser.readline().decode('ascii')
        print(serialString)

    writeString = '1sj0000' + str(jogStepSize)
    ELLser.write((writeString).encode('utf-8'))
    time.sleep(0.2)
    if ELLser.in_waiting > 0:
        serialString = ELLser.readline().decode('ascii')
        print(serialString)

    ELLser.write(("1gj" + "\n").encode('utf-8'))
    time.sleep(0.1)
    if ELLser.in_waiting > 0:
        serialString = ELLser.readline().decode('ascii')
        print('Jog step size = ' + str(round((int(serialString.strip()[3:], 16) / 143360 * 360), 2)) + ' deg\n')

    ELLser.write(('1ho' + '\n').encode('utf-8'))
    time.sleep(1)
    if ELLser.in_waiting > 0:
        serialString = ELLser.readline().decode('ascii')

    ELLser.write(('1gp' + "\n").encode('utf-8'))
    time.sleep(0.2)
    if ELLser.in_waiting > 0:
        serialString = ELLser.readline().decode('ascii')
        pos0 = serialtoDeg(serialString)
        if pos0 > 143360:
            pos0 = 0
        print('Starting position of linear polariser = ' + str(pos0) + ' deg\n')

    # ELL14 setup has consumed ~1-2 s; Arduino should be ready, but swallow
    # any remaining boot banner to be safe.
    wait_for_arduino_ready(ARDser)

    print('Loop starts \n\n')
    time.sleep(1)
    powers = []

    polariserAngles = np.arange(0, 180, jogStepDeg)

    for idx in tqdm(polariserAngles):
        time.sleep(0.5)
        pol = read_power(ARDser)                        # <-- robust power read
        print('\n Power meter = ' + str(pol) + ' V')
        powers.append(pol)

        ELLser.write(('1fw' + '\n').encode('utf-8'))
        time.sleep(0.2)
        if ELLser.in_waiting > 0:
            serialString = ELLser.readline().decode('ascii')
            pos0 = round(serialtoDeg(serialString))
            if pos0 > 143360:
                pos0 = 0
            print(' Current position of linear polariser = ' + str(pos0) + ' deg\n')

    ELLser.reset_input_buffer()
    ELLser.flushInput()
    ELLser.flushOutput()

    ARDser.reset_input_buffer()
    ARDser.flushInput()
    ARDser.flushOutput()

    ELLser.close()
    ARDser.close()

    # -------------------------------------------------------------------------
    # FIT AND PLOT
    # -------------------------------------------------------------------------
    plt.close('all')
    degrees = np.pi / 180
    polariserAngles = np.arange(0, 180, jogStepDeg)
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(121)
    plt.plot(polariserAngles, powers, 'ro')
    plt.xlabel('Polariser angle (deg)')
    plt.ylabel('Laser power (V)')

    def model_f(theta, p1, p2, p3, p4):
        return (p1 * np.cos(theta * degrees - p3))**2 + (p2 * np.sin(theta * degrees - p3))**2 + p4

    popt, pcov = curve_fit(
        model_f, polariserAngles, powers,
        bounds=([0, 0, 0, 0], [np.max(powers) * 1.5, np.min(powers) * 1.5 + 1e-2, 1 * np.pi, 0.01]))

    fitParams.append(popt.copy())
    fitCovs.append(pcov.copy())
    rawScans.append((np.asarray(polariserAngles, dtype=float), np.asarray(powers, dtype=float)))

    Emax, Emin, alpha, offset = popt
    Emaxs.append(Emax)
    Emins.append(Emin)

    fittingAngles = np.arange(0, 180, 1)
    plt.plot(fittingAngles, model_f(fittingAngles, Emax, Emin, alpha, offset), '--b')
    plt.ylim(0, np.max(powers) * 1.1)
    print('\n Ellipse semi major axis angle = ' + str(np.round(alpha * 180 / np.pi)) + ' degrees \n')

    ax = fig.add_subplot(122, aspect='auto')
    e1 = patches.Ellipse((0, 0), Emax / 2, Emin / 2,
                         angle=alpha * 180 / np.pi, linewidth=2, fill=False, zorder=1)
    ax.add_patch(e1)
    ax.set_xlim([-0.5, 0.5])
    ax.set_ylim([-0.5, 0.5])
    ax.axis('off')
    plt.suptitle('Ellipse semi major axis = ' + str(np.round(alpha * 180 / np.pi)) + ' deg, '
                 + 'Emax = ' + str(np.round(Emax, 2)) + ', Emin = ' + str(np.round(Emin, 2)))

    print('Fitted Emax = ' + str(np.round(Emax, 2)))
    print('Fitted Emin = ' + str(np.round(Emin, 2)))

    # -------------------------------------------------------------------------
    # SAVE PER-STEP DATA
    # -------------------------------------------------------------------------
    foldername = '/' + str(polStepNumber).zfill(3) + ' HWP = ' + str(hwp) + '  QWP = ' + str(qwp)
    step_path = Path(saveDir + foldername)
    step_path.mkdir(exist_ok=True)

    np.save(step_path / 'polariserAngles', polariserAngles)
    np.save(step_path / 'powers', powers)

    plt.savefig(saveDir + '/' + str(polStepNumber) + '__HWP = ' + str(hwp).zfill(3)
                + '  QWP = ' + str(qwp).zfill(3) + ' fit and ellipse.png')

    if Emax > Emin:
        a, b = Emax, Emin
    else:
        a, b = Emin, Emax

    ellip = b / a * 100
    percentageEllipticity.append(np.round(ellip, 2))
    polEllipseAngle.append(alpha * 180 / np.pi)


# =============================================================================
# SAVE BLOCK
# =============================================================================
plt.close('all')

plt.figure()
plt.plot(np.asarray(percentageEllipticity), 'ro')
plt.title('Percentage Ellipticity')
plt.savefig(saveDir + '/Percentage Ellipticity.png')
np.save(saveDir + '/Percentage Ellipticity', percentageEllipticity)

plt.figure()
plt.plot(np.array(polEllipseAngle) - np.asarray(expectedEllipseAngles) % 90, 'go')
plt.title('Difference between expected vs measured ellipse angles')
np.save(saveDir + '/alphas', polEllipseAngle)

np.save(saveDir + '/fitParams', np.asarray(fitParams))
np.save(saveDir + '/fitCovs',   np.asarray(fitCovs))
np.save(saveDir + '/expectedEllipseAngles', np.asarray(expectedEllipseAngles))
np.savez(saveDir + '/rawScans',
         polariserAngles=np.asarray(polariserAngles, dtype=float),
         powers=np.asarray([p for (_, p) in rawScans], dtype=float))

# Grid of E-field ellipses
fig, axs = plt.subplots(2, 7, figsize=(30, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace=.5, wspace=.1)
axs = axs.ravel()
polEllipseAngles = np.array(polEllipseAngle) - 0
for idx in range(n):
    e1 = patches.Ellipse((0, 0), Emaxs[idx], Emins[idx],
                         angle=polEllipseAngles[idx], linewidth=2, fill=False, zorder=1)
    axs[idx].add_patch(e1)
    axs[idx].set_xlim([-1.5, 1.5])
    axs[idx].set_ylim([-1.5, 1.5])
    axs[idx].axis('off')
    axs[idx].set_title(str(np.round(polEllipseAngles[idx], 1)))
plt.suptitle('pSHG polarisation electric field ellipses\nSequence used: ' + calibrationFile)
plt.savefig(saveDir + '/pSHG polarisation E-field ellipses.png')

# Grid of intensity ellipses
fig, axs = plt.subplots(2, 7, figsize=(30, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace=.5, wspace=.1)
axs = axs.ravel()
polEllipseAngles = np.array(polEllipseAngle) - 105
for idx in range(n):
    e1 = patches.Ellipse((0, 0), Emaxs[idx]**2, Emins[idx]**2,
                         angle=polEllipseAngles[idx], linewidth=2, fill=False, zorder=1)
    axs[idx].add_patch(e1)
    axs[idx].set_xlim([-1.5, 1.5])
    axs[idx].set_ylim([-1.5, 1.5])
    axs[idx].axis('off')
    axs[idx].set_title(str(np.round(polEllipseAngles[idx], 1)))
plt.suptitle('pSHG polarisation intensity ellipses\nSequence used: ' + calibrationFile)
plt.savefig(saveDir + '/pSHG polarisation intensity ellipses.png')

plt.close('all')

import winsound
frequency = 1000
duration = 200
winsound.Beep(int(frequency / 4), int(duration * 2))
winsound.Beep(int(frequency / 4), int(duration * 2))
print('\n **ACQUISITION FINISHED SUCCESSFULLY**')

path = os.path.realpath(saveDir)
os.startfile(path)
