"""
bfp_handedness_oracle.py   (grid-calibrated)
============================================
Physically-anchored handedness (signed-S3) oracle for the polarisation state at
the microscope back focal plane, as a function of the QWP and HWP dial angles.

Parameters fit against the FULL 777-point AllPolScan grid (HWP 0-180,
QWP 0-100, 5 deg steps) measured at the BFP:

    azimuth RMS residual = 0.99 deg  (99% within 5 deg)
    |S3|    RMS residual  = 0.11
    microscope           = single linear retarder, ~0.64 wave (validated)

The rotating linear polariser is handedness-blind, so the calibration stores
only |S3|.  This module supplies the SIGN from the calibrated forward chain

        E_bfp = M_mic . HWP(dial) . QWP(dial) . E_laser

giving  S3_signed = HANDEDNESS_SIGN * sign(model_S3) * |S3|_measured  -- the
clean replacement for the |S3|-only line in synthetic_birefringence_v2.py.

Conventions match synthetic_birefringence_v2.py (retarder_jones, S3=-2 Im).

HANDEDNESS_SIGN
---------------
The grid is handedness-blind: the fit is identical under conjugation (all S3
flipped).  For a LINEAR focal target the global sign washes out of the
correction -- only self-consistency matters, now guaranteed.  +1 is a fine
default.  The absolute sense is pinned only by an element of known handedness
(the dual-run with a known QWP); if it disagrees, flip the sign below.
"""

import os
import numpy as np

# ===========================================================================
# USER SETTINGS
# ===========================================================================
QWP_SIGN, QWP_OFFSET, QWP_RET = -1, -22.24, 0.2491
HWP_SIGN, HWP_OFFSET, HWP_RET = -1,  52.83, 0.5456
MIC_FAST, MIC_RET             = 76.16, 0.6414
LASER_AZ           = 86.5
BENCH_TO_BFP_PHI   = 38.17
INCLUDE_MICROSCOPE = True
HANDEDNESS_SIGN    = +1

# ===========================================================================
def retarder_jones(delta_rad, fa_deg):
    th = np.radians(fa_deg); c, s = np.cos(th), np.sin(th)
    ep = np.exp(-1j*delta_rad/2.0); em = np.exp(+1j*delta_rad/2.0)
    return np.array([[ep*c**2+em*s**2, (ep-em)*c*s],
                     [(ep-em)*c*s,     ep*s**2+em*c**2]])

def jones_to_stokes_norm(E):
    Ex, Ey = E[0], E[1]
    s0 = abs(Ex)**2 + abs(Ey)**2
    return (s0, (abs(Ex)**2-abs(Ey)**2)/s0,
            2*np.real(Ex*np.conj(Ey))/s0, -2*np.imag(Ex*np.conj(Ey))/s0)

def bfp_state(qwp_deg, hwp_deg):
    E = np.array([np.cos(np.radians(LASER_AZ)), np.sin(np.radians(LASER_AZ))], complex)
    E = retarder_jones(2*np.pi*QWP_RET, QWP_SIGN*qwp_deg+QWP_OFFSET) @ E
    E = retarder_jones(2*np.pi*HWP_RET, HWP_SIGN*hwp_deg+HWP_OFFSET) @ E
    if INCLUDE_MICROSCOPE:
        E = retarder_jones(2*np.pi*MIC_RET, MIC_FAST) @ E
    return E

def bfp_stokes(qwp_deg, hwp_deg):
    _, s1, s2, s3 = jones_to_stokes_norm(bfp_state(qwp_deg, hwp_deg))
    return s1, s2, HANDEDNESS_SIGN*s3

def s3_sign(qwp_deg, hwp_deg):
    return float(np.sign(bfp_stokes(qwp_deg, hwp_deg)[2]))

def generator_s3_sign(hwp_deg, qwp_deg, gen_input_deg=0.0):
    """Drop-in for synthetic_birefringence_v2.generator_s3_sign. Arg order
    (hwp, qwp) matches the original call sites; gen_input_deg ignored."""
    h = np.atleast_1d(np.asarray(hwp_deg, float))
    q = np.atleast_1d(np.asarray(qwp_deg, float))
    out = np.empty(np.broadcast(h, q).shape, float)
    it = np.nditer([h, q, out], flags=['multi_index'],
                   op_flags=[['readonly'], ['readonly'], ['writeonly']])
    for hh, qq, oo in it:
        oo[...] = s3_sign(float(qq), float(hh))
    return float(out.ravel()[0]) if (np.ndim(hwp_deg) == 0 and np.ndim(qwp_deg) == 0) else out

def build_signed_calibration(cal_dir='.'):
    """Return (S1, S2, S3_signed) flat arrays aligned to HWPAngles/QWPAngles.
    Drop-in for the |S3|-only block in synthetic_birefringence_v2.py."""
    L = lambda n: np.load(os.path.join(cal_dir, n))
    hwp = L('HWPAngles.npy').astype(float); qwp = L('QWPAngles.npy').astype(float)
    emax = L('Emaxs.npy'); emin = L('Emins.npy'); alpha = L('alphas.npy')
    S0 = emax**2 + emin**2
    S1 = (emax**2 - emin**2)*np.cos(2*alpha)/S0
    S2 = (emax**2 - emin**2)*np.sin(2*alpha)/S0
    S3abs = np.sqrt(np.maximum(0.0, 1.0 - S1**2 - S2**2))
    # s3_sign already carries HANDEDNESS_SIGN, so do NOT multiply it again here.
    sign = np.array([s3_sign(qwp[i], hwp[i]) for i in range(len(qwp))])
    return S1, S2, sign*S3abs

if __name__ == '__main__':
    cal = '.' if os.path.exists('HWPAngles.npy') else \
          ('Calibration data' if os.path.isdir('Calibration data') else None)
    if cal:
        S1, S2, S3s = build_signed_calibration(cal)
        print(f'signed calibration: {len(S3s)} points, '
              f'{np.mean(S3s>0)*100:.0f}% +ve / {np.mean(S3s<0)*100:.0f}% -ve')
    else:
        print('place the five .npy files beside this script to build the '
              'signed calibration; oracle functions import fine without them.')
