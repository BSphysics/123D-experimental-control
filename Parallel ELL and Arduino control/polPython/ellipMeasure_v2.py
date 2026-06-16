# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 13:38:46 2023
Hardened for the FrameSync Arduino firmware, June 2026

@author: BES (b.sherlock@exeter.ac.uk)

Controls an ELL14 (address '1', commands prefixed '1') on COM8 and reads a
power-meter voltage from the Arduino on COM6.

------------------------------------------------------------------------------
WHY THIS VERSION EXISTS
------------------------------------------------------------------------------
The Arduino now runs the FrameSync sketch (on/off/ping/FRAME_DONE). Two
consequences for this script:

  1. Opening COM6 auto-resets the board, so it prints its boot banner
     ("FW:FrameSync_INT_v1_READY") a beat AFTER reset_input_buffer() runs.
     The old code read that banner as the first power value -> ValueError.
     -> Fixed here: wait_for_arduino_ready() swallows the banner, and a read
        timeout means nothing ever blocks forever.

  2. The FrameSync sketch has NO 'pol' handler and does no analogRead, so it
     returns nothing for 'pol'. The old polarisation firmware must have had a
     'pol' -> analogRead -> Serial.println(volts) command. Until that handler
     is back in the firmware there is no power value for Python to parse.
     -> read_power() now skips non-numeric lines and, if the board stays silent,
        raises a clear message naming the cause instead of crashing on float().

To restore real readings, add this back into the sketch's serial handler
(it sits happily alongside on/off/ping and does NOT touch the frame ISR):

    if (InBytes == "pol") {
      int raw = analogRead(A0);            // <-- your power-meter input pin
      float volts = raw * (5.0 / 1023.0);  // <-- match your old scaling/AREF
      Serial.println(volts, 4);
    }
"""
import os
import numpy as np
import serial
import time
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib import patches

degrees = np.pi / 180
serialString = ""

# --- ELL14 (timeout added so reads can't block) -----------------------------
ELLser = serial.Serial(
    port='COM8', baudrate=9600,
    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
    timeout=0.2)
ELLser.reset_input_buffer()
ELLser.flushInput()
ELLser.flushOutput()

# --- Arduino (timeout added: previously none -> readline() blocked forever) --
ARDser = serial.Serial(port='COM6', baudrate=9600, timeout=1)
ARDser.reset_input_buffer()
ARDser.flushInput()
ARDser.flushOutput()


def degreestoHex(deg):
    pulses = int(deg / 360 * 143360)   # 143360 pulses == 360 deg on the ELL14
    hexPulses = hex(pulses).upper()
    return hexPulses[2:]


jogStepDeg = 20
jogStepSize = str(degreestoHex(jogStepDeg))
if len(jogStepSize) < 4:
    jogStepSize = jogStepSize.zfill(4)


def serialtoDeg(serialString):
    pos = round((int(serialString.strip()[3:], 16) / 143360 * 360), 2)
    return pos


# =============================================================================
# ARDUINO HELPERS (new)
# =============================================================================
def wait_for_arduino_ready(timeout=3.0):
    """Opening the port resets the Arduino; swallow its boot banner so it
    doesn't get read as the first power value."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        raw = ARDser.readline()
        if raw:
            line = raw.decode('ascii', errors='ignore').strip()
            if line.startswith('FW:'):
                print('Arduino ready: ' + line)
                break
    ARDser.reset_input_buffer()


def read_power(timeout=2.0, attempts=3):
    """Ask the Arduino for a power-meter reading and return it as a float.

    Sends 'pol\\n' (the FrameSync sketch reads until '\\n') and reads replies
    until one parses as a number, skipping status/banner lines. If the board
    never returns a number, raises a clear error naming the likely cause.
    """
    for attempt in range(1, attempts + 1):
        ARDser.reset_input_buffer()          # drop anything stale before asking
        ARDser.write(b'pol\n')
        t0 = time.time()
        while time.time() - t0 < timeout:
            raw = ARDser.readline()
            if not raw:
                continue
            line = raw.decode('ascii', errors='ignore').strip()
            if line == '':
                continue
            try:
                return float(line)
            except ValueError:
                # banner / TRIGGERED / ARMED / pong / FRAME_DONE etc. -> ignore
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
# ELL14 SETUP
# =============================================================================
ELLser.write(('1in' + '\n').encode('utf-8'))
time.sleep(0.2)
if ELLser.in_waiting > 0:
    serialString = ELLser.readline().decode('ascii')
    print(serialString)

writeString = '1sj0000' + str(jogStepSize)      # Set jog step size
ELLser.write((writeString).encode('utf-8'))
time.sleep(0.2)
if ELLser.in_waiting > 0:
    serialString = ELLser.readline().decode('ascii')
    print(serialString)

ELLser.write(("1gj" + "\n").encode('utf-8'))     # Confirm jog step size
time.sleep(0.1)
if ELLser.in_waiting > 0:
    serialString = ELLser.readline().decode('ascii')
    print('Jog step size = ' + str(round((int(serialString.strip()[3:], 16) / 143360 * 360), 2)) + ' deg\n')

ELLser.write(('1ho' + '\n').encode('utf-8'))     # Home
time.sleep(1)
if ELLser.in_waiting > 0:
    serialString = ELLser.readline().decode('ascii')

ELLser.write(('1gp' + "\n").encode('utf-8'))     # Confirm home position
time.sleep(0.2)
if ELLser.in_waiting > 0:
    serialString = ELLser.readline().decode('ascii')
    pos0 = serialtoDeg(serialString)
    if pos0 > 143360:
        pos0 = 0
    print('Starting position of linear polariser = ' + str(pos0) + ' deg\n')

# Now that ELL setup has used up a couple of seconds, the Arduino has finished
# booting -> clear its banner before we start asking for power readings.
wait_for_arduino_ready()

print('Loop starts \n\n')
time.sleep(1)
powers = []

polariserAngles = np.arange(0, 180, jogStepDeg)

for idx in tqdm(polariserAngles):
    time.sleep(0.5)
    pol = read_power()                              # <-- robust power read
    print('\n Power meter = ' + str(pol) + ' V')
    powers.append(pol)

    ELLser.write(('1fw' + '\n').encode('utf-8'))    # Jog step
    time.sleep(0.2)
    if ELLser.in_waiting > 0:
        serialString = ELLser.readline().decode('ascii')
        pos0 = round(serialtoDeg(serialString))
        if pos0 > 143360:
            pos0 = 0
        print(' Current position of linear polariser = ' + str(pos0) + ' deg\n')

ELLser.close()
ARDser.close()

#%%
plt.close('all')
degrees = np.pi / 180
polariserAngles = np.arange(0, 180, jogStepDeg)
fig = plt.figure(figsize=(12, 6))
ax = fig.add_subplot(121)
plt.plot(polariserAngles, powers, 'ro')
plt.xlabel('Polariser Angle (deg)')


def model_f(theta, p1, p2, p3, p4):
    return (p1 * np.cos(theta * degrees - p3))**2 + (p2 * np.sin(theta * degrees - p3))**2 + p4


popt, pcov = curve_fit(
    model_f, polariserAngles, powers,
    bounds=([0, 0, 0, 0], [np.max(powers) * 1.5, np.min(powers) * 1.2 + 1e-5, 1 * np.pi, 0.01]))

Emax, Emin, alpha, offset = popt
fittingAngles = np.arange(0, 180, 1)

plt.plot(fittingAngles, model_f(fittingAngles, Emax, Emin, alpha, offset), '--b')
plt.ylim(0, np.max(powers) * 1.1)
print('\n Ellipse semi major axis angle = ' + str(np.round(alpha * 180 / np.pi, 1)) + ' degrees \n')

ax = fig.add_subplot(122, aspect='auto')
e1 = patches.Ellipse((0, 0), Emax / 2, Emin / 2,
                     angle=alpha * 180 / np.pi, linewidth=2, fill=False, zorder=1)
ax.add_patch(e1)
ax.set_xlim([-0.5, 0.5])
ax.set_ylim([-0.5, 0.5])
ax.axis('off')
plt.suptitle('Ellipse semi major axis = ' + str(np.round(alpha * 180 / np.pi)) + ' deg, '
             + 'Emax = ' + str(np.round(Emax, 2)) + ', Emin = ' + str(np.round(Emin, 2)))

print('Fitted Emax = ' + str(np.round(Emax, 3)))
print('Fitted Emin = ' + str(np.round(Emin, 3)))
print('Fitted offset = ' + str(np.round(offset, 3)))

#%% Save the data so that fitting routines can be optimised offline
saveData = 1

if saveData > 0:
    
    # from datetime import datetime
    today = datetime.today()

    # Folder for all measurements taken today
    date_folder = (
        f"Polarisation measurements "
        f"{today.year}_{today.month:02d}_{today.day:02d}"
    )

    # Subfolder for this specific run
    time_folder = (
        f"{today.hour:02d}_{today.minute:02d}_{today.second:02d}"
        f"__ellipMeasure_v2 data"    )

    base_dir = Path(r"D:\2_user_data\Ben")

    # Daily folder
    daily_path = base_dir / date_folder
    daily_path.mkdir(parents=True, exist_ok=True)

    # Run-specific folder
    data_path = daily_path / time_folder
    data_path.mkdir(exist_ok=True)

    saveDir = str(data_path)

    data_path = Path(saveDir)

    if not os.path.exists(data_path):
        os.mkdir(data_path)
    # today = datetime.today()
    # datestamp = (str(today.year) + '_' + str(today.month) + '_' + str(today.day) + '_'
    #              + str(today.hour).zfill(2) + str(today.minute).zfill(2))
    # saveDir = r'D:\!User files\Ben\2024\Polarisation measurements' + r'\ ' + datestamp

    # folderName = ' polarisation after HWP092 and QWP079'

    # data_path = saveDir + folderName
    # data_path = Path(data_path)
    # if not os.path.exists(data_path):
    #     os.mkdir(data_path)

    np.save(data_path / 'polariserAngles', polariserAngles)
    np.save(data_path / 'powers', powers)

    # data_path = []
    # data_path = saveDir + folderName
    plt.savefig(str(data_path) + '/fit and ellipse.png')

#%%

