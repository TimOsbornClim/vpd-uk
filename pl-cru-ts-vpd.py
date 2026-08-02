# -*- coding: utf-8 -*-


"""
Example script to extract CRU TS temperature and vapour pressure
for a single grid cell and calculate vapour pressure deficit (VPD).

Requires:
    cru-ts-functions.py

Input files:
    CRU TS monthly NetCDF files containing:
        tmp  = mean temperature (degC)
        vap  = vapour pressure (hPa)

Output:
    pandas DataFrame with columns:
        tmp
        vap
        vpd
        vpd_kPa
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from cru_ts_functions import extract_cru_ts

from climate_analysis_functions import seasonal_mean

from statsmodels.nonparametric.smoothers_lowess import lowess

# ------------------------------------------------------------------
#%% User settings
# ------------------------------------------------------------------

# Location of interest
lat = 52.63
lon = 1.30

# Period to extract
start_year = 1901
end_year = 2025

# CRU TS files
cru_ts_path = "/Users/f055/Documents/data/CRU-TS/"
tmp_file = "cru-ts-v4.10-1901-2025-tmp-chunk.nc"
vap_file = "cru-ts-v4.10-1901-2025-vap-chunk.nc"

tmp_file = cru_ts_path + tmp_file
vap_file = cru_ts_path + vap_file


# ------------------------------------------------------------------
#%% Extract monthly mean temperature
# ------------------------------------------------------------------

# Returns a pandas Series:
#
#     date          value
#     1950-01-16    ...
#     1950-02-15    ...
#
# The series name will be "tmp"

tmp = extract_cru_ts(
    lat=lat,
    lon=lon,
    ncfile=tmp_file,
    varname="tmp",
    start_year=start_year,
    end_year=end_year,
)

# ------------------------------------------------------------------
#%% Extract monthly mean vapour pressure
# ------------------------------------------------------------------

# CRU TS vapour pressure ("vap") is actual vapour pressure, in hPa.

vap = extract_cru_ts(
    lat=lat,
    lon=lon,
    ncfile=vap_file,
    varname="vap",
    start_year=start_year,
    end_year=end_year,
)


# ------------------------------------------------------------------
#%% Combine variables into a single DataFrame
# ------------------------------------------------------------------

# Resulting columns:
#
#     tmp
#     vap
#
# indexed by monthly timestamps

df = pd.concat([tmp, vap], axis=1)


# ------------------------------------------------------------------
#%% Calculate saturation vapour pressure
# ------------------------------------------------------------------

# Saturation vapour pressure (hPa) calculated from monthly mean
# temperature using the Magnus/Tetens approximation.
#
# Note:
#     This computes e_s(Tmean).
#     Because saturation vapour pressure is nonlinear in temperature,
#     VPD calculated from monthly means is a slight underestimate of
#     the true monthly mean VPD (typically a few percent).

df["es"] = (
    6.112 *
    np.exp(
        17.67 * df["tmp"] /
        (df["tmp"] + 243.5)
    )
)


# ------------------------------------------------------------------
#%% Calculate vapour pressure deficit
# ------------------------------------------------------------------

# VPD = saturation vapour pressure - actual vapour pressure
#
# Units:
#     hPa

df["vpd"] = df["es"] - df["vap"]

# Replace any negative values with zero

df["vpd"] = df["vpd"].clip(lower=0.0)


# ------------------------------------------------------------------
#%% Convert to kPa
# ------------------------------------------------------------------

# Many plant-physiology and hydrology studies report
# VPD in kPa rather than hPa.

df["vpd_kPa"] = df["vpd"] / 10.0


# ------------------------------------------------------------------
#%% Example output
# ------------------------------------------------------------------

print(df.head())

# ------------------------------------------------------------------
# Optional: save to CSV
# ------------------------------------------------------------------

# df.to_csv("norwich_vpd_timeseries.csv")




# ----------------------------------------------------------
#%% Create monthly timeseries plots
# ----------------------------------------------------------

# ----------------------------------------------------------
# Select period to plot
# ----------------------------------------------------------

plot_df = df.loc["2000":"2025"]

# ------------------------------------------------------------------
# Get grid-cell location from metadata
# ------------------------------------------------------------------

grid_lat = tmp.attrs["grid_lat"]
grid_lon = tmp.attrs["grid_lon"]

location_string = (
    f"CRU TS grid cell "
    f"({grid_lat:.2f}°N, {grid_lon:.2f}°E)"
)

# ----------------------------------------------------------
# Create figure
# ----------------------------------------------------------

fig, axes = plt.subplots(
    nrows=3,
    ncols=1,
    figsize=(12, 8),
    sharex=True
)

# ----------------------------------------------------------
# Mean temperature
# ----------------------------------------------------------

axes[0].plot(
    plot_df.index,
    plot_df["tmp"],
    color="tab:red",
    lw=0.8
)

axes[0].set_ylabel("Temperature (°C)")
axes[0].set_title(location_string)
axes[0].grid(True, alpha=0.3)

# ----------------------------------------------------------
# Vapour pressure
# ----------------------------------------------------------

axes[1].plot(
    plot_df.index,
    plot_df["vap"],
    color="tab:blue",
    lw=0.8
)

axes[1].set_ylabel("Vapour pressure (hPa)")
axes[1].grid(True, alpha=0.3)

# ----------------------------------------------------------
# Vapour pressure deficit
# ----------------------------------------------------------

axes[2].plot(
    plot_df.index,
    plot_df["vpd"],
    color="tab:green",
    lw=0.8
)

axes[2].set_ylabel("VPD (hPa)")
axes[2].set_xlabel("Year")
axes[2].grid(True, alpha=0.3)

# ----------------------------------------------------------
# Tidy up
# ----------------------------------------------------------

fig.tight_layout()

plt.show()



# ----------------------------------------------------------
#%% Create annual cyle plots
# ----------------------------------------------------------

import matplotlib.pyplot as plt

# ------------------------------------------------------------------
# Select period
# ------------------------------------------------------------------

plot_df = df.loc["2000":"2025"]

# ------------------------------------------------------------------
# Calculate monthly climatology statistics
# ------------------------------------------------------------------

grouped = plot_df.groupby(plot_df.index.month)

clim_mean = grouped.mean()
clim_std  = grouped.std()
clim_min  = grouped.min()
clim_max  = grouped.max()

months = range(1, 13)

month_names = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

# ------------------------------------------------------------------
# Get grid-cell location from metadata
# ------------------------------------------------------------------

grid_lat = tmp.attrs["grid_lat"]
grid_lon = tmp.attrs["grid_lon"]

location_string = (
    f"CRU TS grid cell "
    f"({grid_lat:.2f}°N, {grid_lon:.2f}°E)"
)

# ------------------------------------------------------------------
# Create figure
# ------------------------------------------------------------------

fig, axes = plt.subplots(
    nrows=3,
    ncols=1,
    figsize=(9, 9),
    sharex=True
)

# ==============================================================
# Temperature
# ==============================================================

# Min-max envelope

axes[0].fill_between(
    months,
    clim_min["tmp"],
    clim_max["tmp"],
    color="tab:red",
    alpha=0.10,
    label="Min-Max"
)

# ±1 sigma envelope

axes[0].fill_between(
    months,
    clim_mean["tmp"] - clim_std["tmp"],
    clim_mean["tmp"] + clim_std["tmp"],
    color="tab:red",
    alpha=0.30,
    label="±1 SD"
)

# Mean

axes[0].plot(
    months,
    clim_mean["tmp"],
    "-o",
    color="tab:red",
    lw=2,
    label="Mean"
)

axes[0].set_ylabel("Temperature (°C)")
axes[0].set_title(
    f"Mean Annual Cycle (2000–2025)\n{location_string}"
)
axes[0].grid(True, alpha=0.3)
axes[0].legend(loc="upper left")

# ==============================================================
# Vapour pressure
# ==============================================================

axes[1].fill_between(
    months,
    clim_min["vap"],
    clim_max["vap"],
    color="tab:blue",
    alpha=0.10
)

axes[1].fill_between(
    months,
    clim_mean["vap"] - clim_std["vap"],
    clim_mean["vap"] + clim_std["vap"],
    color="tab:blue",
    alpha=0.30
)

axes[1].plot(
    months,
    clim_mean["vap"],
    "-o",
    color="tab:blue",
    lw=2
)

axes[1].set_ylabel("Vapour Pressure (hPa)")
axes[1].grid(True, alpha=0.3)

# ==============================================================
# Vapour pressure deficit
# ==============================================================

axes[2].fill_between(
    months,
    clim_min["vpd"],
    clim_max["vpd"],
    color="tab:green",
    alpha=0.10
)

axes[2].fill_between(
    months,
    clim_mean["vpd"] - clim_std["vpd"],
    clim_mean["vpd"] + clim_std["vpd"],
    color="tab:green",
    alpha=0.30
)

axes[2].plot(
    months,
    clim_mean["vpd"],
    "-o",
    color="tab:green",
    lw=2
)

axes[2].set_ylabel("VPD (hPa)")
axes[2].set_xlabel("Month")
axes[2].grid(True, alpha=0.3)

# ------------------------------------------------------------------
# Month labels
# ------------------------------------------------------------------

axes[2].set_xticks(months)
axes[2].set_xticklabels(month_names)

# ------------------------------------------------------------------
# Tidy up
# ------------------------------------------------------------------

fig.tight_layout()

plt.show()







# ----------------------------------------------------------
#%% Create seasonal-mean timeseries plots
# ----------------------------------------------------------

seas_name = "March-June"
seas_def = [3,4,5,6]

#seas_name = "March-July"
#seas_def = [3,4,5,6,7]

tmp_seas = seasonal_mean(tmp, seas_def)
vap_seas = seasonal_mean(vap, seas_def)
vpd_seas = seasonal_mean(df["vpd"], seas_def)
print(tmp_seas.head())

fig, axes = plt.subplots(
    3, 1,
    figsize=(10,8),
    sharex=True
)

axes[0].plot(
    tmp_seas.index,
    tmp_seas.values,
    color="tab:red"
)

axes[0].set_ylabel("Temperature (°C)")
axes[0].grid(True, alpha=0.3)

axes[1].plot(
    vap_seas.index,
    vap_seas.values,
    color="tab:blue"
)

axes[1].set_ylabel("Vapour Pressure (hPa)")
axes[1].grid(True, alpha=0.3)

axes[2].plot(
    vpd_seas.index,
    vpd_seas.values,
    color="tab:green"
)

axes[2].set_ylabel("VPD (hPa)")
axes[2].set_xlabel("Year")
axes[2].grid(True, alpha=0.3)

fig.suptitle(
    f"Seasonal Averages ({seas_name})\n"
    f"CRU TS Grid Cell ({grid_lat:.2f}°N, {grid_lon:.2f}°E)"
)

plt.tight_layout()
plt.show()







# ----------------------------------------------------------
#%% Create seasonal-mean timeseries plots, with smoothed line too
# ----------------------------------------------------------

seas_name = "March-June"
seas_def = [3,4,5,6]

#seas_name = "March-July"
#seas_def = [3,4,5,6,7]

vpd_seas = seasonal_mean(df["vpd"], seas_def)
print(vpd_seas.head())


# ----------------------------------------------------------
# Parameters
# ----------------------------------------------------------

smooth_years = 20
nboot = 1000

# ----------------------------------------------------------
# Prepare data
# ----------------------------------------------------------

x = vpd_seas.index.values.astype(float)
y = vpd_seas.values

# Fraction of data used by LOESS
# Approximately equivalent to a smooth_years window

frac = smooth_years / len(x)

# ----------------------------------------------------------
# LOESS smooth
# ----------------------------------------------------------

y_loess = lowess(
    y,
    x,
    frac=frac,
    return_sorted=False
)

# ----------------------------------------------------------
# Bootstrap confidence intervals
# ----------------------------------------------------------

residuals = y - y_loess

boot_loess = np.zeros((nboot, len(y)))

for iboot in range(nboot):

    # Resample residuals with replacement

    boot_resid = np.random.choice(
        residuals,
        size=len(residuals),
        replace=True
    )

    y_boot = y_loess + boot_resid

    boot_loess[iboot, :] = lowess(
        y_boot,
        x,
        frac=frac,
        return_sorted=False
    )

# 95% confidence interval

ci_lower = np.percentile(
    boot_loess,
    2.5,
    axis=0
)

ci_upper = np.percentile(
    boot_loess,
    97.5,
    axis=0
)

# ----------------------------------------------------------
# Plot
# ----------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(10,4)
)

# Bootstrap confidence band

ax.fill_between(
    x,
    ci_lower,
    ci_upper,
    color="darkgreen",
    alpha=0.15,
    label="95% bootstrap CI"
)

# Raw seasonal values

ax.plot(
    x,
    y,
    color="lightgreen",
    lw=0.8,
    label=f"{seas_name} mean"
)

# LOESS smooth

ax.plot(
    x,
    y_loess,
    color="darkgreen",
    lw=3,
    label=f"{smooth_years}-yr LOESS"
)

ax.set_ylabel("VPD (hPa)")
ax.set_xlabel("Year")

ax.grid(
    True,
    alpha=0.3
)

ax.legend()

fig.suptitle(
    f"Seasonal VPD ({seas_name})\n"
    f"CRU TS Grid Cell "
    f"({grid_lat:.2f}°N, {grid_lon:.2f}°E)"
)

fig.tight_layout()

plt.show()







# ----------------------------------------------------------
#%% Create seasonal-mean timeseries plots, with smoothed line
# too, and block bootstrapped uncertainty on the smooth line
# ----------------------------------------------------------

seas_name = "March-June"
seas_def = [3,4,5,6]

#seas_name = "March-July"
#seas_def = [3,4,5,6,7]

vpd_seas = seasonal_mean(df["vpd"], seas_def)
print(vpd_seas.head())


# ----------------------------------------------------------
# Parameters
# ----------------------------------------------------------

smooth_years = 20
nboot = 1000       # usually choose 1000

# ----------------------------------------------------------
# Prepare data
# ----------------------------------------------------------

x = vpd_seas.index.values.astype(float)
y = vpd_seas.values

# Fraction of data used by LOESS
# Approximately equivalent to a smooth_years window

frac = smooth_years / len(x)

# ----------------------------------------------------------
# LOESS smooth
# ----------------------------------------------------------

y_loess = lowess(
    y,
    x,
    frac=frac,
    return_sorted=False
)

# ----------------------------------------------------------
# Bootstrap confidence intervals
# ----------------------------------------------------------

def moving_block_bootstrap(residuals, block_length):

    n = len(residuals)

    # All possible starting points
    starts = np.arange(n - block_length + 1)

    bootstrap = []

    while len(bootstrap) < n:

        start = np.random.choice(starts)

        block = residuals[
            start:start + block_length
        ]

        bootstrap.extend(block)

    return np.array(bootstrap[:n])




block_length = 5

residuals = y - y_loess

boot_loess = np.zeros((nboot, len(y)))

for iboot in range(nboot):

    # Resample residuals with replacement (block bootstrap)

    boot_resid = moving_block_bootstrap(
        residuals,
        block_length=5
        )

    y_boot = y_loess + boot_resid

    boot_loess[iboot, :] = lowess(
        y_boot,
        x,
        frac=frac,
        return_sorted=False
    )

# 95% confidence interval

ci_lower = np.percentile(
    boot_loess,
    2.5,
    axis=0
)

ci_upper = np.percentile(
    boot_loess,
    97.5,
    axis=0
)

# ----------------------------------------------------------
# Plot
# ----------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(10,4)
)

# Bootstrap confidence band

ax.fill_between(
    x,
    ci_lower,
    ci_upper,
    color="darkgreen",
    alpha=0.15,
    label="95% bootstrap CI"
)

# Raw seasonal values

ax.plot(
    x,
    y,
    color="dimgrey",
    lw=0.8,
    label=f"{seas_name} mean"
)

# LOESS smooth

ax.plot(
    x,
    y_loess,
    color="darkgreen",
    lw=3,
    label=f"{smooth_years}-yr LOESS"
)

ax.set_ylabel("VPD (hPa)")
ax.set_xlabel("Year")

ax.grid(
    True,
    alpha=0.3
)

ax.legend()

fig.suptitle(
    f"Seasonal VPD ({seas_name})\n"
    f"CRU TS Grid Cell "
    f"({grid_lat:.2f}°N, {grid_lon:.2f}°E)"
)

fig.tight_layout()

plt.show()






