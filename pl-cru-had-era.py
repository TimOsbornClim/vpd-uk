# -*- coding: utf-8 -*-


"""
Script to calculate VPD from CRU-TS grid cell, HadUK-Grid river basin
average, and ERA5 grid cell, then compare and plot them together.
"""




# ------------------------------------------------------------------
#%% Get packages and functions
# ------------------------------------------------------------------


import numpy as np
import pandas as pd
import xarray as xr

import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.feature as cfeature

from statsmodels.nonparametric.smoothers_lowess import lowess

# These are my own functions

from cru_ts_functions import extract_cru_ts

from era5_functions import extract_era5

from hadukgrid_functions import extract_haduk_region

from climate_analysis_functions import seasonal_mean
from climate_analysis_functions import saturation_vapour_pressure




# ------------------------------------------------------------------
#%% User settings
# ------------------------------------------------------------------


# What season to focus on?

#seas_name = "April"
#seas_def = [4]

#seas_name = "March-May"
#seas_def = [3,4,5]

#seas_name = "March-June"
#seas_def = [3,4,5,6]

#seas_name = "March-July"
#seas_def = [3,4,5,6,7]

#seas_name = "Febraury-July"
#seas_def = [2,3,4,5,6,7]

seas_name = "April-July"
seas_def = [4,5,6,7]

# Adjust means to match HadUK?
# 0 = no adjustment (not yet suppoprted)
# 1 = means adjusted by additive offset
# 2 = means adjusted by ultiplicative scaling factor
# 3 = means and SDs adjusted by offset then scaling then offset

adjust_means = 3

# CRU-TS settings

# CRU-TS Location of interest (it find closest grid cell)
lat = 52.63
lon = 1.30

# CRU-TS Period to extract
cru_start_year = 1901
cru_end_year = 2025

# CRU-TS files
cru_ts_path = "/Users/f055/Documents/data/CRU-TS/"
cru_tmp_file = "cru-ts-v4.10-1901-2025-tmp-chunk.nc"
cru_vap_file = "cru-ts-v4.10-1901-2025-vap-chunk.nc"

cru_tmp_file = cru_ts_path + cru_tmp_file
cru_vap_file = cru_ts_path + cru_vap_file


# ERA5 settings

# Location of interest
era_lat = 52.75
era_lon = 1.25

# Period to extract
era_start_year = 1950     # not much upper air data before 1950, WWII data issues too
era_end_year = 2026

# ERA5 files
era5_path = "/Users/f055/Documents/data/ERA5/"

# If we have a specific file (e.g. subset of years)

#era5_file = (
#    f"era5_monthly_t2m_d2m_"
#    f"lat{lat:.2f}_lon{lon:.2f}_"
#    f"{start_year}01-{end_year}12.nc"
#)

# Full period file

era5_file = (
    f"era5_monthly_t2m_d2m_"
    f"lat{era_lat:.2f}_lon{era_lon:.2f}_194001-202612.nc"
)

era5_file = era5_path + era5_file


# HadUK-Grid settings

# Region of interest
had_regname = "Anglian"

# Period to extract
had_start_year = 1961
had_end_year = 2025

# HadUK-GRid files
hadukgrid_path = "/Users/f055/Documents/data/HadUK-Grid/"
had_tmp_file = "tas_hadukgrid_uk_river_mon_188401-202512.nc"
had_vap_file = "pv_hadukgrid_uk_river_mon_196101-202512.nc"

had_tmp_file = hadukgrid_path + had_tmp_file
had_vap_file = hadukgrid_path + had_vap_file

# List available region names, to help with choosing one

ds = xr.open_dataset(had_vap_file)

for chars in ds["geo_region"].values:
    print("".join(chars.astype(str)).strip())






# ------------------------------------------------------------------
#%% Extract CRU-TS monthly mean temperature ad vapour pressure
# ------------------------------------------------------------------


# Example script to extract CRU TS temperature and vapour pressure
# for a single grid cell and calculate vapour pressure deficit (VPD).
#
# Requires:
#    cru_ts_functions.py
#
# Input files:
#    CRU TS monthly NetCDF files containing:
#        tmp  = mean temperature (degC)
#        vap  = vapour pressure (hPa)
#
# Output:
#    pandas DataFrame with columns:
#        tmp
#        vap
#        vpd
#        vpd_kPa

# Returns a pandas Series:
#
#     date          value
#     1950-01-16    ...
#     1950-02-15    ...
#
# The series name will be "tmp"

cru_tmp = extract_cru_ts(
    lat=lat,
    lon=lon,
    ncfile=cru_tmp_file,
    varname="tmp",
    start_year=cru_start_year,
    end_year=cru_end_year,
)

# CRU TS vapour pressure ("vap") is actual vapour pressure, in hPa.

cru_vap = extract_cru_ts(
    lat=lat,
    lon=lon,
    ncfile=cru_vap_file,
    varname="vap",
    start_year=cru_start_year,
    end_year=cru_end_year,
)


# ------------------------------------------------------------------
# Combine variables into a single DataFrame
# ------------------------------------------------------------------

# Resulting columns:
#
#     tmp
#     vap
#
# indexed by monthly timestamps

cru_df = pd.concat([cru_tmp, cru_vap], axis=1)




# ------------------------------------------------------------------
#%% Calculate CRU-TS saturation vapour pressure and VPD
# ------------------------------------------------------------------

# Saturation vapour pressure (hPa) calculated from monthly mean
# temperature using the Magnus/Tetens approximation.
#
# Note:
#     This computes e_s(Tmean).
#     Because saturation vapour pressure is nonlinear in temperature,
#     VPD calculated from monthly means is a slight underestimate of
#     the true monthly mean VPD (typically a few percent).

cru_df["es"] = saturation_vapour_pressure(cru_df["tmp"])


# ------------------------------------------------------------------
# Calculate vapour pressure deficit
# ------------------------------------------------------------------

# VPD = saturation vapour pressure - actual vapour pressure
#
# Units:
#     hPa

cru_df["vpd"] = cru_df["es"] - cru_df["vap"]

# Replace any negative values with zero

cru_df["vpd"] = cru_df["vpd"].clip(lower=0.0)





# ------------------------------------------------------------------
#%% Example output
# ------------------------------------------------------------------

print(cru_df.head())

# ------------------------------------------------------------------
# Optional: save to CSV
# ------------------------------------------------------------------

# cru_df.to_csv("cru-ts_norwich_vpd_timeseries.csv")




# ----------------------------------------------------------
#%% Create seasonal-mean timeseries
# ----------------------------------------------------------

cru_vpd_seas = seasonal_mean(cru_df["vpd"], seas_def)
print(cru_vpd_seas.head())




# ------------------------------------------------------------------
#%% Extract ERA5 monthly mean temperature and dewpoint temperature
# ------------------------------------------------------------------

# Example script to extract ERA5 temperature and dewpoint temperature
# for a single grid cell and calculate vapour pressure deficit (VPD).
#
# Requires:
#    era5_functions.py
#
# Input files:
#    ERA5 monthly NetCDF file containing two variables in one file:
#        t2m  = mean temperature (K)
#        d2m  = mean dewpoint temperature (K)
#
# Output:
#    pandas DataFrame with columns:
#        tmp
#        vap
#        dew
#        vpd
#        vpd_kPa

# Returns a pandas Series:
#
#     date          value
#     1950-01-16    ...
#     1950-02-15    ...
#
# The series name will be "tmp"

era_tmp = extract_era5(
    lat=era_lat,
    lon=era_lon,
    ncfile=era5_file,
    varname="t2m",
    start_year=era_start_year,
    end_year=era_end_year
)

era_d2m = extract_era5(
    lat=era_lat,
    lon=era_lon,
    ncfile=era5_file,
    varname="d2m",
    start_year=era_start_year,
    end_year=era_end_year
)


# ------------------------------------------------------------------
# Combine variables into a single DataFrame
# ------------------------------------------------------------------

# Resulting columns:
#
#     tmp
#     vap
#
# indexed by monthly timestamps

# Standardise names to match CRU-TS workflow

era_tmp.name = "tmp"
era_d2m.name = "dpt"

era_df = pd.concat([era_tmp, era_d2m], axis=1)




# ------------------------------------------------------------------
#%% Calculate ERA5 saturation vapour pressure and VPD
# ------------------------------------------------------------------

# Saturation vapour pressure (hPa) calculated from monthly mean
# temperature using the Magnus/Tetens approximation.
#
# Note:
#     This computes e_s(Tmean).
#     Because saturation vapour pressure is nonlinear in temperature,
#     VPD calculated from monthly means is a slight underestimate of
#     the true monthly mean VPD (typically a few percent).

era_df["es"] = saturation_vapour_pressure(era_df["tmp"])

# Also calcluate actual vapour pressure

era_df["vap"] = saturation_vapour_pressure(era_df["dpt"])


# ------------------------------------------------------------------
# Calculate vapour pressure deficit
# ------------------------------------------------------------------

# VPD = saturation vapour pressure - actual vapour pressure
#
# Units:
#     hPa

era_df["vpd"] = era_df["es"] - era_df["vap"]

# Replace any negative values with zero

era_df["vpd"] = era_df["vpd"].clip(lower=0.0)




# ------------------------------------------------------------------
#%% Example output
# ------------------------------------------------------------------

print(era_df.head())

# ------------------------------------------------------------------
# Optional: save to CSV
# ------------------------------------------------------------------

# df.to_csv("era5_norwich_vpd_timeseries.csv")




# ----------------------------------------------------------
#%% Create seasonal-mean timeseries
# ----------------------------------------------------------

era_vpd_seas = seasonal_mean(era_df["vpd"], seas_def)
print(era_vpd_seas.head())







# ------------------------------------------------------------------
#%% Extract HadUK-Grid regional series monthly mean temperature and vapour pressure
# ------------------------------------------------------------------

# Example script to extract HadUK-Grid temperature and vapour pressure
# for a single region and calculate vapour pressure deficit (VPD).
#
# Requires:
#    hadukgrid_functions.py
#
# Input files:
#    HadUK-Grid monthly NetCDF files containing pre-computed regional
#    averages of:
#        tmp  = mean temperature (degC)
#        vap  = vapour pressure (hPa)
#
# Output:
#    pandas DataFrame with columns:
#        tmp
#        vap
#        vpd
#        vpd_kPa

# Returns a pandas Series:
#
#     date          value
#     1950-01-16    ...
#     1950-02-15    ...
#
# The series name will be "tmp"

had_tmp = extract_haduk_region(
    ncfile=had_tmp_file,
    region_name=had_regname,
    start_year=had_start_year,
    end_year=had_end_year
)

# HadUK-Grid vapour pressure ("vap") is actual vapour pressure, in hPa.

had_vap = extract_haduk_region(
    ncfile=had_vap_file,
    region_name=had_regname,
    start_year=had_start_year,
    end_year=had_end_year
)


# ------------------------------------------------------------------
# Combine variables into a single DataFrame
# ------------------------------------------------------------------

# Resulting columns:
#
#     tmp
#     vap
#
# indexed by monthly timestamps

had_df = pd.concat([had_tmp, had_vap], axis=1)

# enforce CRU-TS variable names (HadUK-Grid uses pv not vap)
had_df.columns = ["tmp", "vap"]




# ------------------------------------------------------------------
#%% Calculate saturation vapour pressure and VPD
# ------------------------------------------------------------------

# Saturation vapour pressure (hPa) calculated from monthly mean
# temperature using the Magnus/Tetens approximation.
#
# Note:
#     This computes e_s(Tmean).
#     Because saturation vapour pressure is nonlinear in temperature,
#     VPD calculated from monthly means is a slight underestimate of
#     the true monthly mean VPD (typically a few percent).

had_df["es"] = saturation_vapour_pressure(had_df["tmp"])

# ------------------------------------------------------------------
# Calculate vapour pressure deficit
# ------------------------------------------------------------------

# VPD = saturation vapour pressure - actual vapour pressure
#
# Units:
#     hPa

had_df["vpd"] = had_df["es"] - had_df["vap"]

# Replace any negative values with zero

had_df["vpd"] = had_df["vpd"].clip(lower=0.0)




# ------------------------------------------------------------------
#%% Example output
# ------------------------------------------------------------------

print(had_df.head())

# ------------------------------------------------------------------
# Optional: save to CSV
# ------------------------------------------------------------------

# had_df.to_csv("HadUK-grid-norwich_vpd_timeseries.csv")




# ----------------------------------------------------------
#%% Create HadUK-Grid seasonal-mean timeseries plots
# ----------------------------------------------------------

had_vpd_seas = seasonal_mean(had_df["vpd"], seas_def)
print(had_vpd_seas.head())




# ----------------------------------------------------------
#%% Combine different dataset's seasonal mean series to enable comparison and plotting
# ----------------------------------------------------------


compare_df = pd.concat(
    [
        cru_vpd_seas.rename("CRU-TS"),
        had_vpd_seas.rename("HadUK"),
        era_vpd_seas.rename("ERA5")
    ],
    axis=1
)






# ----------------------------------------------------------
#%% Compare different datasets
# ----------------------------------------------------------

# ------------------------------------------------------------------
# Pairwise correlations (full overlap for each pair)
# ------------------------------------------------------------------

corr_pairwise = compare_df.corr()

print("\nPairwise correlations (full overlap period for each pair)")
print(corr_pairwise)

# ------------------------------------------------------------------
# Common overlap period
# ------------------------------------------------------------------

common_df = compare_df.dropna()

print("\nCommon overlap period:")
print(f"{common_df.index.min()}-{common_df.index.max()}")

# ------------------------------------------------------------------
# Correlations over common overlap period
# ------------------------------------------------------------------

corr_common = common_df.corr()

print("\nCorrelations over common overlap period")
print(corr_common)

# ------------------------------------------------------------------
# Means over common overlap period
# ------------------------------------------------------------------

mean_common = common_df.mean()

print("\nMeans over common overlap period")
print(mean_common)



# ------------------------------------------------------------------
# Adjust CRU-TS and ERA5 means to match HadUK
# ------------------------------------------------------------------

# Create adjusted dataframe (includes unadjusted series too)

compare_adj_df = compare_df.copy()


# Means

had_mean = common_df["HadUK"].mean()
cru_mean = common_df["CRU-TS"].mean()
era_mean = common_df["ERA5"].mean()

# Standard deviations

had_sd = common_df["HadUK"].std()
cru_sd = common_df["CRU-TS"].std()
era_sd = common_df["ERA5"].std()

print("\nCommon-period statistics")

print(f"HadUK  Mean={had_mean:.3f}  SD={had_sd:.3f}")
print(f"CRU    Mean={cru_mean:.3f}  SD={cru_sd:.3f}")
print(f"ERA5   Mean={era_mean:.3f}  SD={era_sd:.3f}")

# Make means adjustments

if adjust_means == 0:

    # no adjustment

    raise ValueError(
        f"No adjustment not yet supported adjust_means={adjust_means}"
    )



elif adjust_means == 1:

    # This adjusts means to match via additive offset

    cru_adjustment = had_mean - cru_mean
    era_adjustment = had_mean - era_mean

    print("\nAdditive mean adjustments")
    print(f"CRU-TS adjustment = {cru_adjustment:.3f} hPa")
    print(f"ERA5 adjustment   = {era_adjustment:.3f} hPa")
    
    compare_adj_df["CRU-TS_adj"] = (
        compare_df["CRU-TS"] + cru_adjustment
    )

    compare_adj_df["ERA5_adj"] = (
        compare_df["ERA5"] + era_adjustment
    )

    compare_adj_df["HadUK_adj"] = (
        compare_df["HadUK"]
    )

    
    
elif adjust_means == 2:

    # This adjusts means to match via scaling factor (may be more suited to zero-bounded variabels)

    cru_adjustment = had_mean / cru_mean
    era_adjustment = had_mean / era_mean

    print("\nMultiplicative mean adjustments")
    print(f"CRU-TS adjustment = {cru_adjustment:.3f} scaling factor")
    print(f"ERA5 adjustment   = {era_adjustment:.3f} scaling factor")
    
    compare_adj_df["CRU-TS_adj"] = (
        compare_df["CRU-TS"] * cru_adjustment
    )

    compare_adj_df["ERA5_adj"] = (
        compare_df["ERA5"] * era_adjustment
    )

    compare_adj_df["HadUK_adj"] = (
        compare_df["HadUK"]
    )


elif adjust_means == 3:

    # This adjusts means and variance to match
    # May need to ensure any negative values are replaced by zero

    cru_adjustment = had_mean - cru_mean
    era_adjustment = had_mean - era_mean

    print("\nAdditive mean adjustments")
    print(f"CRU-TS adjustment = {cru_adjustment:.3f} hPa")
    print(f"ERA5 adjustment   = {era_adjustment:.3f} hPa")
    
    cru_sdadjustment = had_sd / cru_sd
    era_sdadjustment = had_sd / era_sd

    print("\Scaling SD adjustments")
    print(f"CRU-TS adjustment = {cru_sdadjustment:.3f}")
    print(f"ERA5 adjustment   = {era_sdadjustment:.3f}")
    
    compare_adj_df["CRU-TS_adj"] = (
        had_mean
        + (compare_df["CRU-TS"] - cru_mean)
        * (had_sd / cru_sd)
    )

    compare_adj_df["ERA5_adj"] = (
        had_mean
        + (compare_df["ERA5"] - era_mean)
        * (had_sd / era_sd)
    )

    compare_adj_df["HadUK_adj"] = compare_df["HadUK"]





else:

    raise ValueError(
        f"Unsupported adjust_means={adjust_means}"
    )



# Sanity check: the means over the common overlap period should now match

check_df = compare_adj_df[
    ["CRU-TS_adj", "HadUK_adj", "ERA5_adj"]
].dropna()

print("\nAdjusted means over common overlap period")

print(check_df.mean())

print("\nAdjusted SDs over common overlap period")

print(check_df.std())




# ------------------------------------------------------------------
# Multi-dataset average
# ------------------------------------------------------------------

compare_adj_df["MULTI"] = (
    compare_adj_df[
        ["CRU-TS_adj", "HadUK_adj", "ERA5_adj"]
    ]
    .mean(axis=1)
)



# ----------------------------------------------------------
#%% Create seasonal-mean timeseries plots, with original data
# ----------------------------------------------------------



fig, ax = plt.subplots(figsize=(10,5))

ax.plot(
    compare_adj_df.index,
    compare_adj_df["CRU-TS"],
    label="CRU-TS"
)

ax.plot(
    compare_adj_df.index,
    compare_adj_df["HadUK"],
    label="HadUK"
)

ax.plot(
    compare_adj_df.index,
    compare_adj_df["ERA5"],
    label="ERA5"
)

ax.set_ylabel("VPD (hPa)")
ax.set_xlabel("Year")

ax.grid(True, alpha=0.3)
ax.legend()

plt.show()





# ----------------------------------------------------------
#%% Create seasonal-mean timeseries plots, with mean-adjusted data
# ----------------------------------------------------------



fig, ax = plt.subplots(figsize=(10,5))

ax.plot(
    compare_adj_df.index,
    compare_adj_df["CRU-TS_adj"],
    label="CRU-TS (mean-adjusted)"
)

ax.plot(
    compare_adj_df.index,
    compare_adj_df["HadUK_adj"],
    label="HadUK"
)

ax.plot(
    compare_adj_df.index,
    compare_adj_df["ERA5_adj"],
    label="ERA5 (mean-adjusted)"
)

ax.set_ylabel("VPD (hPa)")
ax.set_xlabel("Year")

ax.grid(True, alpha=0.3)
ax.legend()

plt.show()






# ----------------------------------------------------------
#%% Create seasonal-mean timeseries plots, with smoothed line too
# ----------------------------------------------------------

# ------------------------------------------------------------------
# Parameters
# ------------------------------------------------------------------

block_length = 5
nboot = 1000
smooth_years = 20

# ------------------------------------------------------------------
# Input series for smoothed line: the multi-dataset mean
# ------------------------------------------------------------------

multi = compare_adj_df["MULTI"].dropna()

x = multi.index.values.astype(float)
y = multi.values

frac = smooth_years / len(x)

# ------------------------------------------------------------------
# LOESS fit
# ------------------------------------------------------------------

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

# ------------------------------------------------------------------
# Block-bootstrap confidence intervals
# ------------------------------------------------------------------

residuals = y - y_loess

boot_loess = np.zeros(
    (nboot, len(y))
)

for iboot in range(nboot):

    boot_resid = moving_block_bootstrap(
        residuals,
        block_length
    )

    y_boot = y_loess + boot_resid

    boot_loess[iboot, :] = lowess(
        y_boot,
        x,
        frac=frac,
        return_sorted=False
    )

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

# ------------------------------------------------------------------
# Plot comparison
# ------------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(10,5)
)

# Individual datasets

ax.plot(
    compare_adj_df.index,
    compare_adj_df["CRU-TS_adj"],
    color="tab:blue",
    lw=1.5,
    alpha=0.7,
    label="CRU-TS"
)

ax.plot(
    compare_adj_df.index,
    compare_adj_df["HadUK_adj"],
    color="tab:orange",
    lw=1.5,
    alpha=0.7,
    label="HadUK-Grid"
)

ax.plot(
    compare_adj_df.index,
    compare_adj_df["ERA5_adj"],
    color="tab:green",
    lw=1.5,
    alpha=0.7,
    label="ERA5"
)

# Bootstrap CI

ax.fill_between(
    x,
    ci_lower,
    ci_upper,
    color="black",
    alpha=0.15,
    label="Sampling uncertainty in long-term changes"
#    label="95% LOESS CI"
)

# Smoothed multi-dataset average

ax.plot(
    x,
    y_loess,
    color="black",
    lw=3,
    label="Underlying long-term climate changes"
#    label=f"{smooth_years}-yr LOESS (dataset mean)"
)

ax.set_ylabel("VPD (hPa)")
ax.set_xlabel("Year")

ax.grid(
    True,
    alpha=0.3
)

ax.legend()

ax.set_title(
    f"Seasonal ({seas_name}) Vapour Pressure Deficit (VPD) for {had_regname} region"
)

fig.text(
    0.01,
    0.010,
    "CRU-TS and ERA5 were linearly transformed to "
    "match the HadUK-Grid mean and standard deviation over the common overlap period.",
    ha="left",
    va="bottom",
    fontsize=8,
    color="0.4"
)

fig.text(
    0.01,
    0.040,
    "Analysis by Climatic Research Unit UEA. "
    "Datasets: CRU-TS (UEA), HadUK-Grid (Met Office), ERA5 (ECMWF). "
    "Only ERA5 currently has data for 2026.",
    ha="left",
    va="bottom",
    fontsize=8,
    color="0.4"
)

plt.tight_layout(rect=[0, 0.06, 1, 1])


# ------------------------------------------------------------------
# Create filename
# ------------------------------------------------------------------

region_safe = had_regname.replace(" ", "_")
season_safe = seas_name.replace(" ", "_")


outfile = (
    f"VPD_{region_safe}_{season_safe}"
    f"_smooth{smooth_years}yr"
    f"_adj{adjust_means}.pdf"
)


# ------------------------------------------------------------------
# Save figure
# ------------------------------------------------------------------

fig.savefig(
    outfile,
    bbox_inches="tight"
)

print(f"Saved: {outfile}")


plt.show()


