"""Re-diagnose ERA5's 10 m wind over a SEA surface, using ERA5's own surface layer.

THE PROBLEM (measured 2026-08-03)
---------------------------------
ERA5's ``u10``/``v10`` are not observations and not a free field: they are DIAGNOSED
from the modelled surface-layer profile using ERA5's OWN LOCAL surface roughness. Over a
0.25 deg (~28 km) cell that happens to cover a 4-6 km lagoon, that roughness is the
land's. Measured on ``data/era5/era5_nj_sandy_sfc.nc``:

    cells over Barnegat Bay   land fraction 0.26-0.90   z0 = 0.195-0.983 m
    genuine ocean cells       land fraction 0.000       z0 = 0.003-0.006 m

i.e. ERA5 diagnoses the bay's wind through a roughness 50-250x the marine value. SFINCS
then applies a MARINE drag law (``cdnrb=3``) to that land-diagnosed wind. The forcing
chain is internally inconsistent, and the bay is where it shows: the model reproduces
only 55% of the observed along-bay tilt, and since setup ~ U^2 that implies a wind ratio
of 0.74 — against a measured bay/ocean ERA5 ratio of 0.77-0.81.

THE CONVERSION
--------------
Standard blending-height argument. Above the surface layer the flow has forgotten the
local roughness, so the wind at a blending height is taken as given; the 10 m wind is
then re-derived downward through a CHARNOCK sea surface:

    U_b    = (u* / kappa) * ln(z_b / z0_era)          from ERA5's own u* and z0
    U_b    = (u*_w / kappa) * ln(z_b / z0_w)          solve for the marine u*_w,
             with z0_w = alpha * u*_w^2 / g + 0.11 nu / u*_w     (iterate)
    U10_w  = (u*_w / kappa) * ln(10 / z0_w)

``alpha = 0.0185`` is ECMWF's own Charnock constant, ``kappa = 0.40``. **No parameter is
fitted to our results.** Direction is preserved — surface-layer veering over 10 m is
second order and ERA5 gives no basis to change it.

THE FALSIFIER — CHECK IT BEFORE SPENDING A RUN
----------------------------------------------
Over genuinely marine cells ERA5's roughness is ALREADY Charnock, so the conversion must
be the IDENTITY there. ``verification_table`` reports the ratio at the three NDBC buoys;
if it is not ~1.00, the implementation is wrong and the arm must be cancelled. A
correction that is ~1 where observations say ERA5 is right, and ~1.3 only where the
roughness is demonstrably wrong, is a physics fix. One that moves everything is tuning.

⚠️ THE BLENDING HEIGHT IS A CHOICE and it is the one soft number here. Sensitivity,
computed by ``blend_sensitivity``: the bay correction runs ~1.27 (40 m) to ~1.41 (100 m),
with 60 m giving ~1.34. Report the band; do not quote 60 m as if it were derived.
"""

from __future__ import annotations

import numpy as np

CHARNOCK = 0.0185      # ECMWF's own value
KAPPA = 0.40
G = 9.80665
NU_AIR = 1.5e-5        # kinematic viscosity, for the smooth-flow term
Z_BLEND = 60.0         # m; see the docstring warning
#: Below this friction velocity the profile is ill-conditioned and the correction is
#: meaningless anyway (it is a calm cell). Left untouched.
USTAR_MIN = 1e-3


def charnock_z0(ustar: np.ndarray, alpha: float = CHARNOCK) -> np.ndarray:
    """Sea-surface roughness from friction velocity (Charnock + smooth-flow term)."""
    u = np.maximum(np.asarray(ustar, float), USTAR_MIN)
    return alpha * u**2 / G + 0.11 * NU_AIR / u


def blend_wind(ustar: np.ndarray, z0: np.ndarray, z_blend: float = Z_BLEND) -> np.ndarray:
    """Wind speed at the blending height from ERA5's own u* and roughness."""
    z0 = np.maximum(np.asarray(z0, float), 1e-6)
    return np.asarray(ustar, float) / KAPPA * np.log(np.maximum(z_blend / z0, 1.0 + 1e-9))


def overwater_ustar(u_blend: np.ndarray, z_blend: float = Z_BLEND,
                    alpha: float = CHARNOCK, iters: int = 40) -> np.ndarray:
    """Marine friction velocity consistent with ``u_blend`` at ``z_blend``.

    Fixed-point on u*_w: z0 depends on u*_w and u*_w depends on z0. Converges in a few
    iterations for storm winds; ``iters`` is a generous cap, not a tuning knob.
    """
    ub = np.asarray(u_blend, float)
    us = np.maximum(ub * KAPPA / np.log(z_blend / 1e-3), USTAR_MIN)   # first guess
    for _ in range(iters):
        z0 = charnock_z0(us, alpha)
        new = ub * KAPPA / np.log(np.maximum(z_blend / z0, 1.0 + 1e-9))
        if np.nanmax(np.abs(new - us)) < 1e-8:
            us = new
            break
        us = new
    return us


def overwater_u10(u10_u, u10_v, ustar, z0, z_blend: float = Z_BLEND,
                  alpha: float = CHARNOCK):
    """ERA5 10 m wind components -> equivalent OVER-WATER 10 m components.

    Returns ``(u, v, ratio)``. Direction is preserved; ``ratio`` is the speed
    multiplier and is the field to inspect — it must be ~1 over genuine ocean.

    Cells where ERA5's own roughness is already marine come back essentially unchanged,
    which is the property that makes this a correction rather than a scaling.
    """
    u = np.asarray(u10_u, float)
    v = np.asarray(u10_v, float)
    spd = np.hypot(u, v)

    ub = blend_wind(ustar, z0, z_blend)
    us_w = overwater_ustar(ub, z_blend, alpha)
    z0_w = charnock_z0(us_w, alpha)
    spd_w = us_w / KAPPA * np.log(np.maximum(10.0 / z0_w, 1.0 + 1e-9))

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(spd > 1e-6, spd_w / spd, 1.0)
    ratio = np.where(np.isfinite(ratio), ratio, 1.0)
    return u * ratio, v * ratio, ratio


def blend_sensitivity(ustar, z0, heights=(40.0, 60.0, 100.0),
                      alpha: float = CHARNOCK) -> dict:
    """Speed multiplier at several blending heights — the honesty check on Z_BLEND.

    The blending height is the one soft parameter in this module. Report this band
    rather than a single number.
    """
    out = {}
    for h in heights:
        ub = blend_wind(ustar, z0, h)
        us_w = overwater_ustar(ub, h, alpha)
        z0_w = charnock_z0(us_w, alpha)
        spd_w = us_w / KAPPA * np.log(np.maximum(10.0 / z0_w, 1.0 + 1e-9))
        spd = np.asarray(ustar, float) / KAPPA * np.log(
            np.maximum(h / np.maximum(np.asarray(z0, float), 1e-6), 1.0 + 1e-9))
        # express against the ERA5 10 m wind implied by its own profile
        spd10 = np.asarray(ustar, float) / KAPPA * np.log(
            np.maximum(10.0 / np.maximum(np.asarray(z0, float), 1e-6), 1.0 + 1e-9))
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where(spd10 > 1e-6, spd_w / spd10, np.nan)
        out[h] = float(np.nanmedian(r))
    return out
