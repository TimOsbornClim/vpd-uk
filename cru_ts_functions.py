#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 22:41:25 2026

@author: f055
"""

"""
Utilities for extracting CRU TS time series.
"""

from pathlib import Path

import pandas as pd
import xarray as xr


def extract_cru_ts(
    lat,
    lon,
    ncfile,
    varname=None,
    start_year=None,
    end_year=None,
):
    """
    Extract a monthly time series from a CRU TS NetCDF file.

    Parameters
    ----------
    lat : float
        Latitude (degrees north)

    lon : float
        Longitude (degrees east, either -180:180 or 0:360)

    ncfile : str or Path
        CRU TS NetCDF file

    varname : str, optional
        Variable name in file.
        If None, inferred from filename.

    start_year, end_year : int, optional
        Year range to extract.

    Returns
    -------
    pandas.Series

    Notes
    -----
    The returned Series has:
        - datetime index
        - variable name as Series name
    """

    ds = xr.open_dataset(ncfile)

    if varname is None:
        varnames = [v for v in ds.data_vars]
        if len(varnames) != 1:
            raise ValueError(
                f"Must specify varname; found variables: {varnames}"
            )
        varname = varnames[0]

    da = ds[varname]

    # ----------------------------------------------------------
    # Longitude handling
    # ----------------------------------------------------------

    file_lon_min = float(ds.lon.min())
    file_lon_max = float(ds.lon.max())

    if file_lon_max > 180:
        # Dataset uses 0-360
        lon_extract = lon % 360
    else:
        # Dataset uses -180 to 180
        lon_extract = ((lon + 180) % 360) - 180

    # ----------------------------------------------------------
    # Extract nearest grid cell
    # ----------------------------------------------------------

    da = da.sel(
        lat=lat,
        lon=lon_extract,
        method="nearest"
    )

    # ----------------------------------------------------------
    # Time subset
    # ----------------------------------------------------------

    if start_year is not None:
        da = da.sel(time=slice(f"{start_year}-01", None))

    if end_year is not None:
        da = da.sel(time=slice(None, f"{end_year}-12"))

    # ----------------------------------------------------------
    # Selected grid coordinates
    # ----------------------------------------------------------

    grid_lat = float(da.lat)
    grid_lon = float(da.lon)

    print(
        f"{varname}: selected grid cell "
        f"({grid_lat:.2f}, {grid_lon:.2f})"
    )

    series = pd.Series(
        da.values,
        index=pd.to_datetime(da.time.values),
        name=varname,
    )

    # ----------------------------------------------------------
    # Add metadata
    # ----------------------------------------------------------
    
    series.attrs = {
        "grid_lat": grid_lat,
        "grid_lon": grid_lon,
    }

    return series
