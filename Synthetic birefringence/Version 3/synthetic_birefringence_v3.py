"""
synthetic_birefringence_v3.py
=============================
Compute the HWP and QWP angles needed to simulate a user-defined uniaxial
retarder using an empirically calibrated HWP + QWP polarisation generator.

WHAT CHANGED FROM v2
--------------------
The rotating linear polariser cannot measure handedness, so the calibration
stores only |S3|.  v2 supplied the missing sign from an *idealised* HWP->QWP
generator, which disagreed with the real rig (wrong plate order, raw dial
angles, no microscope) on ~half the grid.  v3 instead gets the sign from the
grid-calibrated forward model in ``bfp_handedness_oracle`` (correct plate
order/offsets/retardances + the ~0.64-wave microscope), validated to ~1 deg
azimuth across all 777 points.

Concretely:
  * the SIGNED S3 calibration is built once at load time as
        S3_signed = sign(model) * |S3|_measured
    (model gives the sign, measurement gives the magnitude), and that signed
    grid is interpolated directly -- smoother and correct through sign flips,
    where |S3| necessarily passes through zero;
  * the search matches signed S3 throughout; no per-search sign guessing;
  * the handedness convention now lives in ONE place,
    ``bfp_handedness_oracle.HANDEDNESS_SIGN`` (the gen_input_deg / oracle_sign
    knobs are gone).

For a LINEAR focal target the global sign cancels from the correction, so the
result is robust to that one remaining convention bit; the dual-run pins its
absolute sense if ever needed.

Usage
-----
    from synthetic_birefringence_v3 import find_retarder_settings
    hwp, qwp, results = find_retarder_settings(
        cal_dir='.', delta_waves=0.25, fa_deg=60.0)
"""

import os
import numpy as np
from scipy.interpolate import RegularGridInterpolator

import bfp_handedness_oracle as oracle


# ---------------------------------------------------------------------------
# Jones / Stokes helpers   (conventions shared with bfp_handedness_oracle)
# ---------------------------------------------------------------------------

def retarder_jones(delta_rad: float, fa_deg: float) -> np.ndarray:
    """Jones matrix of a linear retarder. delta_rad in radians, fa_deg in deg."""
    theta = np.radians(fa_deg)
    c, s = np.cos(theta), np.sin(theta)
    ep = np.exp(-1j * delta_rad / 2)
    em = np.exp(+1j * delta_rad / 2)
    return np.array([
        [ep * c**2 + em * s**2, (ep - em) * c * s],
        [(ep - em) * c * s,     ep * s**2 + em * c**2],
    ])


def jones_to_stokes_norm(E: np.ndarray) -> tuple:
    """Normalised Stokes (s0 unnormalised; s1,s2,s3 /s0). s3 = -2 Im(Ex Ey*)."""
    Ex, Ey = E[0], E[1]
    s0 = abs(Ex)**2 + abs(Ey)**2
    s1 = (abs(Ex)**2 - abs(Ey)**2) / s0
    s2 = 2 * np.real(Ex * np.conj(Ey)) / s0
    s3 = -2 * np.imag(Ex * np.conj(Ey)) / s0
    return s0, s1, s2, s3


def stokes_to_ellipse(s1: float, s2: float, s3: float) -> tuple:
    """Normalised Stokes -> (psi_deg [0,180), chi_deg [-45,45], dolp)."""
    psi_deg = (0.5 * np.degrees(np.arctan2(s2, s1))) % 180
    chi_deg = 0.5 * np.degrees(np.arcsin(np.clip(s3, -1.0, 1.0)))
    dolp    = np.sqrt(s1**2 + s2**2)
    return psi_deg, chi_deg, dolp


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class SyntheticRetarder:
    """Compute HWP / QWP settings that emulate a target uniaxial retarder.

    Parameters
    ----------
    cal_dir : str
        Folder containing the five calibration .npy files (and, optionally, a
        cached ``S3_signed.npy``).
    phi_start, phi_step, n_steps
        Input linear-polarisation sequence (degrees / count).
    s3_weight : float
        Weight on the S3 mismatch in the matching cost. Default 1.0.
    interp_step_deg : float
        Resolution of the interpolated search grid (deg). Default 1.0.
    handedness_oracle : bool
        True (default): match *signed* S3 using the calibrated oracle sign.
        False: original |S3|-only behaviour (handedness left to chance).
    use_cached_signed : bool
        True (default): if ``S3_signed.npy`` exists in cal_dir, load it instead
        of recomputing via the oracle. The two are identical; the cache is just
        faster. (Delete the cache after changing the oracle's HANDEDNESS_SIGN.)

    Notes
    -----
    The global handedness convention is set ONCE in
    ``bfp_handedness_oracle.HANDEDNESS_SIGN`` -- not here.
    """

    def __init__(
        self,
        cal_dir: str = '.',
        phi_start: float = 43.6,
        phi_step: float = 14.85,
        n_steps: int = 14,
        s3_weight: float = 1.0,
        interp_step_deg: float = 1.0,
        handedness_oracle: bool = True,
        use_cached_signed: bool = True,
    ):
        self.phi_start         = phi_start
        self.phi_step          = phi_step
        self.n_steps           = n_steps
        self.s3_weight         = s3_weight
        self.interp_step_deg   = interp_step_deg
        self.handedness_oracle = handedness_oracle
        self.use_cached_signed = use_cached_signed

        self._load_calibration(cal_dir)
        self._build_search_grid()

    # ------------------------------------------------------------------
    # Calibration loading
    # ------------------------------------------------------------------

    def _load_calibration(self, cal_dir: str) -> None:
        def load(name):
            return np.load(os.path.join(cal_dir, name))

        hwp_raw   = load('HWPAngles.npy').astype(float)
        qwp_raw   = load('QWPAngles.npy').astype(float)
        emax_raw  = load('Emaxs.npy').astype(float)
        emin_raw  = load('Emins.npy').astype(float)
        alpha_raw = load('alphas.npy').astype(float)   # radians

        # Linear Stokes from the measured ellipse (BFP analyser frame)
        S0 = emax_raw**2 + emin_raw**2
        S1 = (emax_raw**2 - emin_raw**2) * np.cos(2 * alpha_raw) / S0
        S2 = (emax_raw**2 - emin_raw**2) * np.sin(2 * alpha_raw) / S0
        S3_abs = np.sqrt(np.maximum(0.0, 1.0 - S1**2 - S2**2))

        # Signed S3: model supplies the sign, measurement the magnitude.
        if self.handedness_oracle:
            cache = os.path.join(cal_dir, 'S3_signed.npy')
            if self.use_cached_signed and os.path.exists(cache):
                S3_signed = np.load(cache).astype(float)
                if S3_signed.shape != S3_abs.shape:
                    raise ValueError(
                        "S3_signed.npy shape does not match the calibration; "
                        "delete the cache to recompute.")
            else:
                # oracle sign already carries HANDEDNESS_SIGN
                sign = oracle.generator_s3_sign(hwp_raw, qwp_raw)
                S3_signed = sign * S3_abs
            self._S3_used = S3_signed
        else:
            self._S3_used = S3_abs

        # Grid axes (data is HWP-major: reshape(n_hwp, n_qwp))
        self.hwp_unique = np.unique(hwp_raw)
        self.qwp_unique = np.unique(qwp_raw)
        n_hwp, n_qwp = len(self.hwp_unique), len(self.qwp_unique)

        self.S1_grid     = S1.reshape(n_hwp, n_qwp)
        self.S2_grid     = S2.reshape(n_hwp, n_qwp)
        self.S3_abs_grid = S3_abs.reshape(n_hwp, n_qwp)
        self.S3_grid     = self._S3_used.reshape(n_hwp, n_qwp)   # signed or |S3|

    def _build_search_grid(self) -> None:
        """Interpolate the calibration onto a fine search grid."""
        step = self.interp_step_deg
        itp_kw = dict(method='linear', bounds_error=False, fill_value=None)
        axes = (self.hwp_unique, self.qwp_unique)

        iS1 = RegularGridInterpolator(axes, self.S1_grid, **itp_kw)
        iS2 = RegularGridInterpolator(axes, self.S2_grid, **itp_kw)
        # Interpolate the SIGNED S3 directly (smooth through sign flips, where
        # |S3| -> 0). With the oracle off this is just |S3|.
        iS3 = RegularGridInterpolator(axes, self.S3_grid, **itp_kw)

        hwp_fine = np.arange(self.hwp_unique[0], self.hwp_unique[-1] + step, step)
        qwp_fine = np.arange(self.qwp_unique[0], self.qwp_unique[-1] + step, step)
        HH, QQ   = np.meshgrid(hwp_fine, qwp_fine, indexing='ij')
        pts      = np.column_stack([HH.ravel(), QQ.ravel()])

        self._fine_hwp = HH.ravel()
        self._fine_qwp = QQ.ravel()
        self._fine_S1  = iS1(pts)
        self._fine_S2  = iS2(pts)
        self._fine_S3  = iS3(pts)   # signed if oracle on, |S3| if off

    # ------------------------------------------------------------------
    # Core matching
    # ------------------------------------------------------------------

    def _find_best_match(self, s1_tgt, s2_tgt, s3_tgt_signed) -> tuple:
        """Nearest calibration point on the Poincaré sphere.

        Oracle on  -> match signed S3 against the (signed) target.
        Oracle off -> match |S3| against |target|.
        """
        w = self.s3_weight
        s3_tgt = s3_tgt_signed if self.handedness_oracle else abs(s3_tgt_signed)
        d2 = ((self._fine_S1 - s1_tgt)**2
              + (self._fine_S2 - s2_tgt)**2
              + w * (self._fine_S3 - s3_tgt)**2)
        best = int(np.argmin(d2))
        return (float(self._fine_hwp[best]),
                float(self._fine_qwp[best]),
                float(np.sqrt(d2[best])))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute(self, delta_deg=None, delta_waves=None, fa_deg=0.0,
                phi_start=None, phi_step=None, n_steps=None) -> list:
        """Find HWP / QWP settings simulating a uniaxial retarder.

        Give the retardance as delta_deg (degrees) OR delta_waves (fraction of
        a wavelength); exactly one. fa_deg is the fast-axis orientation.
        """
        if delta_deg is None and delta_waves is None:
            raise ValueError("Specify either delta_deg or delta_waves.")
        if delta_deg is not None and delta_waves is not None:
            raise ValueError("Specify only one of delta_deg or delta_waves.")
        if delta_waves is not None:
            delta_deg = 360.0 * delta_waves
        delta_rad = np.radians(delta_deg)

        phi_start_ = phi_start if phi_start is not None else self.phi_start
        phi_step_  = phi_step  if phi_step  is not None else self.phi_step
        n_steps_   = n_steps   if n_steps   is not None else self.n_steps
        phi_inputs = phi_start_ + np.arange(n_steps_) * phi_step_

        J = retarder_jones(delta_rad, fa_deg)
        results = []
        for i, phi_in in enumerate(phi_inputs):
            phi_rad = np.radians(phi_in % 180.0)
            E_in    = np.array([np.cos(phi_rad), np.sin(phi_rad)], dtype=complex)
            E_out   = J @ E_in

            _, s1t, s2t, s3t = jones_to_stokes_norm(E_out)
            psi, chi, dolp   = stokes_to_ellipse(s1t, s2t, s3t)

            hwp, qwp, err = self._find_best_match(s1t, s2t, s3t)

            # Handedness the chosen (HWP, QWP) is predicted to produce at the BFP
            gen_sign = oracle.s3_sign(qwp, hwp)

            results.append({
                'step':         i + 1,
                'phi_in':       float(phi_in % 180.0),
                'hwp':          hwp,
                'qwp':          qwp,
                'alpha_target': psi,
                'chi_target':   chi,
                'dolp_target':  dolp,
                'match_error':  err,
                's1_target':    s1t,
                's2_target':    s2t,
                's3_target':    s3t,
                'gen_s3_sign':  gen_sign,
            })
        return results

    def print_results(self, results: list) -> None:
        print()
        print("=" * 72)
        print(f"  Synthetic birefringence (v3) — {len(results)} input states")
        print("=" * 72)
        hdr = f"{'#':>3}  {'phi_in':>7}  {'a_tgt':>7}  {'chi_tgt':>7}  {'DOLP':>6}  "
        hdr += f"{'HWP':>6}  {'QWP':>6}  {'d(PS)':>7}  {'hand':>4}"
        print(hdr)
        print("-" * 72)
        for r in results:
            flag = " !" if abs(r['match_error']) > 0.07 else ""
            hand = 'R' if r['gen_s3_sign'] > 0 else 'L' if r['gen_s3_sign'] < 0 else '-'
            print(f"{r['step']:>3}  {r['phi_in']:>6.1f}  {r['alpha_target']:>6.1f}  "
                  f"{r['chi_target']:>6.1f}  {r['dolp_target']:>6.4f}  "
                  f"{r['hwp']:>6.1f}  {r['qwp']:>6.1f}  {r['match_error']:>7.4f}  "
                  f"{hand:>4}{flag}")
        print("-" * 72)
        errs = [r['match_error'] for r in results]
        print(f"  Mean d = {np.mean(errs):.4f}   Max d = {np.max(errs):.4f}")
        crit = [r for r in results if abs(r['s3_target']) > 0.4]
        if crit:
            bad = sum(1 for r in crit
                      if np.sign(r['s3_target']) != np.sign(r.get('gen_s3_sign', 0)))
            tag = "OK" if bad == 0 else f"{bad} MISMATCH"
            print(f"  Handedness (|S3|>0.4 steps): {len(crit)} critical, "
                  f"{len(crit) - bad}/{len(crit)} consistent  [{tag}]")
        print("=" * 72)
        print()

    def hwp_qwp_arrays(self, results: list) -> tuple:
        return (np.array([r['hwp'] for r in results]),
                np.array([r['qwp'] for r in results]))

    def plot_results(self, results: list) -> None:
        """Target ellipses, Poincaré S1-S2 scatter, and angle table."""
        import matplotlib.pyplot as plt
        from matplotlib.patches import Ellipse as MEllipse

        n = len(results)
        fig = plt.figure(figsize=(14, 8))
        fig.suptitle("Synthetic birefringence (v3) — results", fontsize=13, y=0.98)
        cols = plt.cm.viridis(np.linspace(0.1, 0.9, n))

        ax1 = fig.add_subplot(1, 3, 1, aspect='equal')
        ax1.set_title("Target polarisation ellipses", fontsize=10)
        R = 0.9
        for i, r in enumerate(results):
            psi = np.radians(r['alpha_target']); chi = np.radians(r['chi_target'])
            a, b = R, R * abs(np.tan(chi))
            ax1.add_patch(MEllipse(xy=(0, 0), width=2*a, height=2*b,
                                   angle=r['alpha_target'], fill=False,
                                   edgecolor=cols[i], linewidth=1.5, alpha=0.8))
            dx, dy = a*np.cos(psi), a*np.sin(psi)
            ax1.plot([-dx, dx], [-dy, dy], color=cols[i], lw=0.6, alpha=0.4)
        ax1.set_xlim(-1.15, 1.15); ax1.set_ylim(-1.15, 1.15)
        ax1.axhline(0, lw=0.4, color='grey'); ax1.axvline(0, lw=0.4, color='grey')
        ax1.set_xlabel("x"); ax1.set_ylabel("y")

        ax2 = fig.add_subplot(1, 3, 2, aspect='equal')
        ax2.set_title("Poincaré S1-S2 projection", fontsize=10)
        tc = np.linspace(0, 2*np.pi, 300)
        ax2.plot(np.cos(tc), np.sin(tc), 'k-', lw=0.5, alpha=0.3)
        ax2.axhline(0, lw=0.4, color='grey'); ax2.axvline(0, lw=0.4, color='grey')
        for i, r in enumerate(results):
            ax2.scatter(r['s1_target'], r['s2_target'], color=cols[i], zorder=3, s=40)
        ax2.set_xlim(-1.15, 1.15); ax2.set_ylim(-1.15, 1.15)
        ax2.set_xlabel("S1"); ax2.set_ylabel("S2")

        ax3 = fig.add_subplot(1, 3, 3); ax3.set_title("HWP / QWP settings", fontsize=10)
        ax3.axis('off')
        col_labels = ["Step", "phi", "a_tgt", "chi", "HWP", "QWP", "d", "hand"]
        data = [[str(r['step']), f"{r['phi_in']:.1f}", f"{r['alpha_target']:.1f}",
                 f"{r['chi_target']:.1f}", f"{r['hwp']:.0f}", f"{r['qwp']:.0f}",
                 f"{r['match_error']:.4f}",
                 ('R' if r['gen_s3_sign'] > 0 else 'L' if r['gen_s3_sign'] < 0 else '-')]
                for r in results]
        tbl = ax3.table(cellText=data, colLabels=col_labels, loc='center', cellLoc='center')
        tbl.auto_set_font_size(False); tbl.set_fontsize(8); tbl.scale(1.0, 1.3)
        for ri, r in enumerate(results):
            err = r['match_error']
            colour = '#d1fae5' if err < 0.03 else '#fef3c7' if err < 0.07 else '#fee2e2'
            for ci in range(len(col_labels)):
                tbl[(ri + 1, ci)].set_facecolor(colour)
        plt.tight_layout(); plt.show()


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse as MEllipse

def plot_ellipse_grid(results, title="BFP polarisation ellipses", cols_per_row=7):
    """
    Plot one polarisation ellipse per step in an n-panel subplot grid.

    Parameters
    ----------
    results : list of dicts
        Output from SyntheticRetarder.compute() or find_retarder_settings().
    title : str
        Figure suptitle.
    cols_per_row : int
        How many columns in the grid (default 7 → 2 rows of 7 for 14 steps).
    """
    n      = len(results)
    ncols  = cols_per_row
    nrows  = int(np.ceil(n / ncols))
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, n))

    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(ncols * 2.2, nrows * 2.2),
                             subplot_kw=dict(aspect='equal'))
    axes = np.array(axes).reshape(nrows, ncols)   # always 2-D
    R = 0.85   # semi-major axis radius in axes units

    for idx, r in enumerate(results):
        row, col = divmod(idx, ncols)
        ax = axes[row, col]

        chi_rad = np.radians(r['chi_target'])
        psi_deg = r['alpha_target']
        psi_rad = np.radians(psi_deg)

        a = R
        b = R * abs(np.tan(chi_rad))   # semi-minor from ellipticity angle

        # Ellipse patch: angle= is CCW rotation of the major axis from x-axis
        ellipse = MEllipse(xy=(0, 0), width=2*a, height=2*b,
                           angle=psi_deg, fill=False,
                           edgecolor=colors[idx], linewidth=1.8)
        ax.add_patch(ellipse)

        # Major-axis tick
        dx, dy = a * np.cos(psi_rad), a * np.sin(psi_rad)
        ax.plot([-dx, dx], [-dy, dy], color=colors[idx], lw=0.8, alpha=0.5)

        # Handedness arrow along the ellipse perimeter
        hand = r.get('gen_s3_sign', 0)
        if hand != 0:
            t0   = psi_rad + np.pi / 2   # point at top of ellipse
            dt   = 0.15 * hand            # small CCW (R, +) or CW (L, -) nudge
            t1   = t0 + dt
            # Parametric ellipse in its own frame, then rotate
            def ellipse_pt(t):
                xe = a * np.cos(t)
                ye = b * np.sin(t)
                xr = xe * np.cos(psi_rad) - ye * np.sin(psi_rad)
                yr = xe * np.sin(psi_rad) + ye * np.cos(psi_rad)
                return xr, yr
            x0, y0 = ellipse_pt(t0)
            x1, y1 = ellipse_pt(t1)
            ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                        arrowprops=dict(arrowstyle="-|>",
                                       color=colors[idx], lw=1.2))

        # Crosshairs and border
        ax.axhline(0, lw=0.3, color='grey', alpha=0.5)
        ax.axvline(0, lw=0.3, color='grey', alpha=0.5)
        ax.set_xlim(-1.1, 1.1); ax.set_ylim(-1.1, 1.1)
        ax.set_xticks([]); ax.set_yticks([])

        # Panel label: step number, orientation angle, ellipticity
        hand_str = 'R' if hand > 0 else ('L' if hand < 0 else '?')
        ax.set_title(
                    f"#{r['step']}  HWP={r['hwp']:.0f}°  QWP={r['qwp']:.0f}°\n"
                    f"ψ={r['alpha_target']:.1f}°  χ={r['chi_target']:.1f}°  {hand_str}",
                    fontsize=7, pad=3
                )

    # Hide any spare axes (if n < nrows*ncols)
    for idx in range(n, nrows * ncols):
        row, col = divmod(idx, ncols)
        axes[row, col].set_visible(False)
    
    fig.suptitle(title, fontsize=12, y=0.97)

    fig.tight_layout()
    plt.show()
    return fig


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def find_retarder_settings(
    cal_dir='.', delta_deg=None, delta_waves=None, fa_deg=0.0,
    phi_start=43.6, phi_step=14.85, n_steps=14,
    s3_weight=1.0, interp_step_deg=1.0,
    handedness_oracle=True, use_cached_signed=True, verbose=True,
) -> tuple:
    """Load calibration, compute settings, optionally print. Returns
    (hwp_array, qwp_array, results)."""
    sr = SyntheticRetarder(
        cal_dir=cal_dir, phi_start=phi_start, phi_step=phi_step, n_steps=n_steps,
        s3_weight=s3_weight, interp_step_deg=interp_step_deg,
        handedness_oracle=handedness_oracle, use_cached_signed=use_cached_signed,
    )
    results = sr.compute(delta_deg=delta_deg, delta_waves=delta_waves, fa_deg=fa_deg)
    if verbose:
        sr.print_results(results)
    hwp, qwp = sr.hwp_qwp_arrays(results)
    return hwp, qwp, results


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    CAL_DIR = '.'   # folder with the five .npy files (+ optional S3_signed.npy)
    print("\n--- lambda/4 waveplate, fast axis at 45 deg ---")
    hwp, qwp, res = find_retarder_settings(
        cal_dir=CAL_DIR, delta_waves=0.25, fa_deg=45.0)
    print("HWP angles:", np.round(hwp, 1))
    print("QWP angles:", np.round(qwp, 1))
    
    # --- Summary plot (3 panels) ---
    sr = SyntheticRetarder(cal_dir=CAL_DIR)
    sr.plot_results(res)
    
    plot_ellipse_grid(res, title="BFP ellipses — λ/4, FA=45°")
    
    
