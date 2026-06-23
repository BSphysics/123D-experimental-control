# -*- coding: utf-8 -*-
"""
Created on Thu Jan  6 16:00:59 2022
Diagnostics added June 2026

@author: BES (b.sherlock@exeter.ac.uk)

Script controls a pair of Thorlabs ELL14s connected via USB -> interface board
-> ELLB bus. ELL '0' (HWP) is prefixed '0', ELL '2' (QWP) is prefixed '2'.

------------------------------------------------------------------------------
DIAGNOSTICS (this version)
------------------------------------------------------------------------------
Everything below logs to console AND to a timestamped .log file (flushed every
line, so the log survives a freeze) plus a per-frame .csv summary. Both land in
the same folder as `fullFileName`. Nothing here changes commanded positions or
loop timing for in-range angles.

What the channels tell you:
  ELL.TX / ELL.RX        every byte sent/received on COM5, with the raw repr
  ELL.STALE_BEFORE       bytes sitting in the ELL buffer before a command
                         (= leftover from the previous move -> bus desync)
  ELL.STATUS             a 'GS' packet (status/error code) instead of 'PO'
  ELL.TIMEOUT            the 3 s spin that feels like "getting stuck"
  ARD.STALE_PRE_TRIG     bytes in the Arduino buffer before we trigger
                         (= stale/early FRAME_DONE -> the retry can double-scan)
  ARD.FRAME_DONE ...leftover=N   N>0 means an extra FRAME_DONE is queued
  FRAME.END flags=...    per-frame timing + anything that went wrong

Toggles are in the DIAGNOSTICS CONFIG block.
"""

import os
import re
import sys
import time
import datetime
import serial
import winsound          # Windows-only; warning beeps on sequence problems
import pandas as pd
from tqdm import tqdm

# fullFileName = r'D:\1_software\Experimental control software\2023_06_22 new pSHG sequence MIRA\2023_06_22 new pSHG sequence MIRA.xlsx'
fullFileName = r'D:\1_software\Experimental control software\Synthetic birefringence\0pt25 waves\delta_waves=0.250_fast_axis=110.xlsx'
# fullFileName = r'D:\1_software\Experimental control software\Synthetic birefringence\FA 50 deg\delta_waves=0.400_fast_axis=50.xlsx'
# fullFileName = r'D:\1_software\Experimental control software\Synthetic birefringence\rotating_linear_pol.xlsx'

dfHWP = pd.read_excel(fullFileName, usecols='C')
dfQWP = pd.read_excel(fullFileName, usecols='D')

frequency = 1000  # beep frequency (Hz)
duration = 200    # beep duration (ms)

# =============================================================================
# DIAGNOSTICS CONFIG
# =============================================================================
DIAG         = True     # master switch for all logging
DRAIN_STALE  = True     # read+log unexpected bytes before a command.
                        #   True  -> diagnoses AND clears contamination (recommended)
                        #   False -> only counts them, leaves them in the buffer
                        #            (use once to confirm the count, then set True)
SLOW_FRAME_S = 2.0      # flag any frame slower than this (nominal ~1.2 s)

_log_dir = os.path.dirname(fullFileName) or os.getcwd()
_stamp   = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_PATH = os.path.join(_log_dir, f'pshg_diag_{_stamp}.log')
CSV_PATH = os.path.join(_log_dir, f'pshg_diag_{_stamp}.csv')

_T0 = time.perf_counter()
_logfile = open(LOG_PATH, 'w', encoding='utf-8') if DIAG else None
_csvfile = open(CSV_PATH, 'w', encoding='utf-8') if DIAG else None
if _csvfile:
    _csvfile.write('frame,hwp_cmd,qwp_cmd,hwp_pos,qwp_pos,hwp_err,qwp_err,'
                   't_hwp_s,t_qwp_s,t_trig_s,t_total_s,trig_attempts,flags\n')
    _csvfile.flush()


def log(event, **fields):
    """Timestamped structured log line -> console + file, flushed immediately."""
    if not DIAG:
        return
    t = time.perf_counter() - _T0
    parts = [f'{t:9.3f}', f'{event:<22}']
    parts += [f'{k}={v}' for k, v in fields.items()]
    line = '  '.join(parts)
    print(line)
    if _logfile:
        _logfile.write(line + '\n')
        _logfile.flush()


def ang_err(measured, target):
    """Wrapped angular error in deg, so 359.5 vs 0 reads as 0.5, not 359.5."""
    return abs((measured - target + 180) % 360 - 180)


# =============================================================================
# SERIAL SETUP
# =============================================================================
serialString = ""

ELLser = serial.Serial(
    port='COM5', baudrate=9600,
    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.2)
ELLser.reset_input_buffer()
ELLser.flushInput()
ELLser.flushOutput()

ARDser = serial.Serial(port='COM6', baudrate=9600, timeout=1)
ARDser.reset_input_buffer()

log('SESSION.START', log=LOG_PATH, csv=CSV_PATH, file=os.path.basename(fullFileName),
    drain_stale=DRAIN_STALE)


# =============================================================================
# CONVERSION HELPERS
# =============================================================================
def degreestoHex(deg):
    """Degrees -> 8-digit hex pulse count for the ELL14.

    Hardened vs the original: wraps into [0, 360) first (so negative or >360
    commanded angles produce a VALID absolute position) and always emits 8
    upper-case hex chars. For in-range positive angles this returns exactly the
    same string the old version did, so nothing changes for those.

    The old version did hex(pulses)[2:], which for a negative pulse count
    produced 'X2EAA'-style garbage -> an invalid 'ma' command -> the ELL never
    replies -> a 3 s ELL.TIMEOUT. If your fast-axis-60 sequence has any negative
    angles, watch the ELL.TX log lines: the `hex=` field will now always be
    clean 8-char hex.
    """
    deg = deg % 360.0                                  # 143360 pulses == 360 deg
    pulses = int(round(deg / 360.0 * 143360))
    return format(pulses & 0xFFFFFFFF, '08X')


def serialtoDeg(serialString):
    m = re.search(r'([0-9A-F]{8})', serialString)
    if not m:
        raise ValueError(f"Bad ELL packet: {repr(serialString)}")
    return round(int(m.group(1), 16) / 143360 * 360, 2)


# =============================================================================
# MOVE / WAIT FUNCTIONS (instrumented)
# =============================================================================
def move_ell(addr, deg, timeout=3.0):
    cmd_hex = degreestoHex(deg)            # already 8 chars; .zfill no longer needed
    cmd = f'{addr}ma{cmd_hex}'

    # --- contamination check: any bytes here are leftovers from a prior move ---
    stale = ELLser.in_waiting
    if stale:
        leftover = ELLser.read(stale) if DRAIN_STALE else b''
        log('ELL.STALE_BEFORE', addr=addr, n=stale, data=repr(leftover))

    log('ELL.TX', addr=addr, deg=deg, hex=cmd_hex, cmd=cmd)
    ELLser.write((cmd + '\n').encode('utf-8'))

    t0 = time.time()
    n_lines = 0
    while time.time() - t0 < timeout:
        raw = ELLser.readline()
        if raw:
            n_lines += 1
            line = raw.decode('ascii', errors='ignore').strip()
            log('ELL.RX', addr=addr, line=line, raw=repr(raw))

            if line.startswith(f'{addr}PO'):
                pos = serialtoDeg(line)
                after = ELLser.in_waiting
                log('ELL.DONE', addr=addr, pos=pos,
                    dt=round(time.time() - t0, 3), lines=n_lines, leftover=after)
                if after:
                    # extra bytes after the PO -> will desync the NEXT command
                    log('ELL.TRAILING', addr=addr, n=after)
                return pos

            if line.startswith(f'{addr}GS'):
                # status packet: '...GS00' is OK, anything else is a fault
                # (e.g. 09 mech.timeout, 0A current error, 0B mech.error)
                log('ELL.STATUS', addr=addr, line=line)

    log('ELL.TIMEOUT', addr=addr, deg=deg,
        waited=round(time.time() - t0, 3), lines=n_lines)
    raise TimeoutError(f'ELL{addr} move to {deg} did not complete')


def wait_for_frame_done(timeout=10):
    """Block until Arduino sends FRAME_DONE. Logs every line it sees."""
    start = time.time()
    while True:
        if ARDser.in_waiting > 0:
            raw = ARDser.readline()
            msg = raw.decode('ascii', errors='ignore').strip()
            log('ARD.RX', msg=msg, raw=repr(raw), t=round(time.time() - start, 3))
            if msg == 'FRAME_DONE':
                return
        if time.time() - start > timeout:
            log('ARD.TIMEOUT', waited=round(time.time() - start, 3))
            raise TimeoutError('No FRAME_DONE received from Arduino')
        time.sleep(0.001)


# =============================================================================
# ELL info / homing helpers (instrumented, behaviour preserved)
# =============================================================================
def ell_query(cmd, timeout=1.5):
    """Send a command, wait up to `timeout` for the first non-empty reply line.

    Replaces the old `time.sleep(0.5); if in_waiting: readline()` pattern, which
    silently kept a stale `serialString` (and could false-trigger sys.exit) if
    the ELL was a touch slow. Same equality checks below, just a robust read.
    """
    ELLser.write((cmd + '\n').encode('utf-8'))
    t0 = time.time()
    while time.time() - t0 < timeout:
        raw = ELLser.readline()
        if raw:
            s = raw.decode('ascii')
            log('ELL.QUERY', cmd=cmd, reply=repr(s))
            return s
    log('ELL.QUERY_TIMEOUT', cmd=cmd)
    return ''


def beep_error(msg):
    for _ in range(3):
        winsound.Beep(frequency, duration)
    log('BEEP_ERROR', msg=msg)
    print('\n'.join(['pSHG sequence ERROR - ' + msg] * 3))


# --- identity checks ---------------------------------------------------------
serialString = ell_query('0in')
if serialString != '0IN0E1140051420211501016800023000\r\n':
    sys.exit('Unexpected response (ELL 0). Terminating script.')

serialString = ell_query('2in')
if serialString != '2IN0E1140064920211501016800023000\r\n':
    sys.exit('Unexpected response (ELL 2). Terminating script.')

# --- home --------------------------------------------------------------------
ell_query('0ho', timeout=3.0)
ell_query('2ho', timeout=3.0)

# --- confirm homing ----------------------------------------------------------
s = ell_query('0gp')
pos0 = serialtoDeg(s) if s else None
print(f'Starting position of HWP = {pos0} deg\n')

s = ell_query('2gp')
pos2 = serialtoDeg(s) if s else None
print(f'Starting position of QWP = {pos2} deg\n')

# NOTE: the move arrays below are built but NOT used by the main loop
#       (the loop rebuilds each command via move_ell). Kept for reference.
HWPMoveArray = ['0ma' + degreestoHex(int(dfHWP.values[i + 2])) for i in range(14)]
QWPMoveArray = ['2ma' + degreestoHex(int(dfQWP.values[i + 2])) for i in range(14)]

ELLser.flushInput()
ELLser.flushOutput()
time.sleep(1)


# =============================================================================
# TRIGGER + RETRY (instrumented)
# =============================================================================
POS_TOL = 1.0          # deg
REARM_DELAY = 0.4      # head-start before first trigger attempt
ATTEMPT_TIMEOUT = 10   # must exceed one frame period (0.7 s) by a clear margin
MAX_TRIES = 4


def trigger_and_wait(idx):
    """Fire trigger; retry only if NO frame scanned. Returns (success, attempts)."""
    for attempt in range(1, MAX_TRIES + 1):

        # Anything already in the buffer BEFORE we trigger is stale (a leftover
        # or early FRAME_DONE). If not cleared, wait_for_frame_done returns on
        # it instantly and the retry logic can scan an EXTRA frame -> desync.
        pre = ARDser.in_waiting
        if pre:
            leftover = ARDser.read(pre) if DRAIN_STALE else b''
            log('ARD.STALE_PRE_TRIG', frame=idx + 1, attempt=attempt,
                n=pre, data=repr(leftover))

        log('ARD.TRIG', frame=idx + 1, attempt=attempt)
        ARDser.write(b'on\n'); time.sleep(0.05); ARDser.write(b'off\n')

        try:
            t0 = time.time()
            wait_for_frame_done(timeout=ATTEMPT_TIMEOUT)
            leftover = ARDser.in_waiting
            log('ARD.FRAME_DONE', frame=idx + 1, attempt=attempt,
                dt=round(time.time() - t0, 3), leftover=leftover)
            if leftover:
                # a second FRAME_DONE queued behind the one we consumed
                log('ARD.EXTRA_DONE', frame=idx + 1, n=leftover)
            return True, attempt
        except TimeoutError:
            log('ARD.DROP', frame=idx + 1, attempt=attempt)
            time.sleep(REARM_DELAY)

    beep_error(f'Frame {idx + 1} FAILED after {MAX_TRIES} tries')
    return False, MAX_TRIES


# =============================================================================
# MAIN LOOP
# =============================================================================
print('Loop starts \n\n')
log('LOOP.START')
time.sleep(1)
ARDser.reset_input_buffer()

try:
    for idx in tqdm(range(14)):
        f_t0 = time.perf_counter()
        pos0 = None
        pos2 = None
        attempts = 0

        HWPdeg = int(dfHWP.values[idx + 2])
        QWPdeg = int(dfQWP.values[idx + 2])
        log('FRAME.START', frame=idx + 1, hwp=HWPdeg, qwp=QWPdeg)

        # ---- HWP -------------------------------------------------------------
        s = time.perf_counter()
        try:
            pos0 = move_ell('0', HWPdeg)
            e = ang_err(pos0, HWPdeg)
            if e > POS_TOL:
                log('FRAME.HWP_MISMATCH', frame=idx + 1, pos=pos0, want=HWPdeg, err=round(e, 2))
                beep_error(f'HWP at {pos0} deg, expected {HWPdeg} (frame {idx + 1})')
        except TimeoutError as exc:
            beep_error(str(exc))
        t_hwp = time.perf_counter() - s

        # ---- QWP -------------------------------------------------------------
        s = time.perf_counter()
        try:
            pos2 = move_ell('2', QWPdeg)
            e = ang_err(pos2, QWPdeg)
            if e > POS_TOL:
                log('FRAME.QWP_MISMATCH', frame=idx + 1, pos=pos2, want=QWPdeg, err=round(e, 2))
                beep_error(f'QWP at {pos2} deg, expected {QWPdeg} (frame {idx + 1})')
        except TimeoutError as exc:
            beep_error(str(exc))
        t_qwp = time.perf_counter() - s

        # ---- trigger acquisition --------------------------------------------
        time.sleep(REARM_DELAY)
        s = time.perf_counter()
        ok, attempts = trigger_and_wait(idx)
        t_trig = time.perf_counter() - s

        # ---- per-frame summary ----------------------------------------------
        t_total = time.perf_counter() - f_t0
        flags = []
        if t_total > SLOW_FRAME_S: flags.append('SLOW')
        if pos0 is None:           flags.append('HWP_TIMEOUT')
        if pos2 is None:           flags.append('QWP_TIMEOUT')
        if not ok:                 flags.append('TRIG_FAIL')
        if attempts > 1:           flags.append(f'RETRY{attempts}')
        flagstr = ','.join(flags) if flags else 'ok'

        log('FRAME.END', frame=idx + 1, t_total=round(t_total, 3),
            t_hwp=round(t_hwp, 3), t_qwp=round(t_qwp, 3),
            t_trig=round(t_trig, 3), attempts=attempts, flags=flagstr)

        if _csvfile:
            he = round(ang_err(pos0, HWPdeg), 2) if pos0 is not None else ''
            qe = round(ang_err(pos2, QWPdeg), 2) if pos2 is not None else ''
            _csvfile.write(
                f'{idx + 1},{HWPdeg},{QWPdeg},{pos0},{pos2},{he},{qe},'
                f'{t_hwp:.3f},{t_qwp:.3f},{t_trig:.3f},{t_total:.3f},'
                f'{attempts},{flagstr}\n')
            _csvfile.flush()

finally:
    # Guarantee ports + log files close even if the loop throws, so the next
    # run isn't blocked by COM5/COM6 still being held open.
    log('LOOP.END')
    ELLser.close()
    ARDser.close()
    if _csvfile:
        _csvfile.close()
    if _logfile:
        _logfile.close()

# Done beep
winsound.Beep(1000, 300)
time.sleep(0.1)
winsound.Beep(600, 300)

#%%
