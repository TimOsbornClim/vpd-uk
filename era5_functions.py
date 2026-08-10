#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 21:13:49 2026

@author: f055
"""


"""
Utilities for downloading ERA5 data

"""


import cdsapi


def download_era5_monthly(
    lat,
    lon,
    outfile,
    start_year=1940,
    end_year=2026,
    buffer_deg=0.25,
):
    """
    Download ERA5 monthly mean temperature and dewpoint temperature.

    Parameters
    ----------
    lat : float
        Latitude (deg N)

    lon : float
        Longitude (deg E)

    outfile : str
        Output NetCDF filename

    start_year : int
        First year

    end_year : int
        Last year

    buffer_deg : float
        Half-width of download box in degrees.

        Download area:

            lat +/- buffer_deg
            lon +/- buffer_deg

    Notes
    -----
    Downloads:

        t2m  = 2 metre temperature
        d2m  = 2 metre dewpoint temperature

    from:

        ERA5 monthly averaged data on single levels

    The downloaded file can subsequently be processed
    using extract_era5().
    """

    client = cdsapi.Client()

    # Convert longitude to ERA5 convention (0-360)

    lon_360 = lon % 360

    north = lat + buffer_deg
    west  = lon_360 - buffer_deg
    south = lat - buffer_deg
    east  = lon_360 + buffer_deg

    area = [north, west, south, east]



    request = {

        "product_type":
            "monthly_averaged_reanalysis",

        "variable": [
            "2m_temperature",
            "2m_dewpoint_temperature",
        ],

        "year": [
            str(y)
            for y in range(start_year, end_year + 1)
        ],

        "month": [
            "01", "02", "03", "04",
            "05", "06", "07", "08",
            "09", "10", "11", "12",
        ],

        "time": "00:00",

        "data_format": "netcdf",

        "area": area,
    }

    print(
        f"Downloading ERA5 monthly data "
        f"({start_year}-{end_year})"
    )

    print(
        f"Area: "
        f"N={north:.2f}, "
        f"W={west:.2f}, "
        f"S={south:.2f}, "
        f"E={east:.2f}"
        )

    client.retrieve(
        "reanalysis-era5-single-levels-monthly-means",
        request,
        outfile
    )

    print(f"Saved to: {outfile}")
    
    
    
    
    
    
    
import pandas as pd
import xarray as xr


def extract_era5(
    lat,
    lon,
    ncfile,
    varname,
    start_year=None,
    end_year=None,
):
    """
    Extract an ERA5 monthly time series from a local NetCDF file.

    Parameters
    ----------
    lat : float
        Latitude (degrees north)

    lon : float
        Longitude (degrees east)

    ncfile : str
        ERA5 NetCDF filename

    varname : str
        Variable name, e.g.

            "t2m"
            "d2m"

    start_year, end_year : int, optional
        Period to extract

    Returns
    -------
    pandas.Series

    Notes
    -----
    Temperature variables are automatically converted
    from Kelvin to Celsius.
    """

    ds = xr.open_dataset(
        ncfile,
        engine="netcdf4"
    )

    da = ds[varname]

    # ----------------------------------------------------------
    # Longitude handling
    # ----------------------------------------------------------

    lon_extract = lon % 360

    # ----------------------------------------------------------
    # Extract nearest ERA5 grid cell
    # ----------------------------------------------------------

    da = da.sel(
        latitude=lat,
        longitude=lon_extract,
        method="nearest"
    )

    # ----------------------------------------------------------
    # Time subset
    # ----------------------------------------------------------

    time_name = "valid_time"

    if start_year is not None:
        da = da.sel(
            {time_name: slice(f"{start_year}-01-01", None)}
        )

    if end_year is not None:
        da = da.sel(
            {time_name: slice(None, f"{end_year}-12-31")}
        )

    # ----------------------------------------------------------
    # Convert temperature variables to Celsius
    # ----------------------------------------------------------

    if varname in ["t2m", "d2m"]:

        da = da - 273.15

    # ----------------------------------------------------------
    # Save selected grid coordinates
    # ----------------------------------------------------------

    grid_lat = float(da.latitude)
    grid_lon = float(da.longitude)

    print(
        f"{varname}: selected ERA5 grid cell "
        f"({grid_lat:.2f}, {grid_lon:.2f})"
    )

    # ----------------------------------------------------------
    # Convert to pandas Series
    # ----------------------------------------------------------

    series = pd.Series(
        da.values,
        index=pd.to_datetime(
            da[time_name].values
        ),
        name=varname
    )

    series.attrs["grid_lat"] = grid_lat
    series.attrs["grid_lon"] = grid_lon

    return series
    
    
    
    
    
        
