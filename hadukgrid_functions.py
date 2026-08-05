#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 22:41:25 2026

@author: f055
"""

"""
Utilities for extracting HadUK-Grid time series.
"""

import pandas as pd
import xarray as xr


def extract_haduk_region(
    ncfile,
    region_name,
    varname=None,
    start_year=None,
    end_year=None,
):
    """
    Extract a HadUK-Grid river-basin regional time series.

    Parameters
    ----------
    ncfile : str
        NetCDF filename.

    region_name : str
        River basin name exactly as stored in geo_region.

    varname : str, optional
        Variable name. If None, infer automatically.

    start_year, end_year : int, optional
        Period to extract.

    Returns
    -------
    pandas.Series
    """

    ds = xr.open_dataset(ncfile)

    # Infer variable name

    if varname is None:

        varnames = list(ds.data_vars)

        # Remove coordinate-like variables

        varnames = [
            v for v in varnames
            if v not in [
                "calendar_year",
                "month_number",
                "season_year",
                "time_bnds",
                "geo_region"
            ]
        ]

        if len(varnames) != 1:
            raise ValueError(
                f"Cannot infer variable name from {varnames}"
            )

        varname = varnames[0]

    # Convert geo_region char array to strings

    basin_names = [
        "".join(chars.astype(str)).strip()
        for chars in ds["geo_region"].values
    ]

    if region_name not in basin_names:

        raise ValueError(
            f"Region '{region_name}' not found.\n"
            f"Available regions:\n{basin_names}"
        )

    region_index = basin_names.index(region_name)

    da = ds[varname].isel(region=region_index)

    # Time subset

    if start_year is not None:
        da = da.sel(time=slice(f"{start_year}-01", None))

    if end_year is not None:
        da = da.sel(time=slice(None, f"{end_year}-12"))

    series = pd.Series(
        da.values,
        index=pd.to_datetime(da.time.values),
        name=varname
    )

    series.attrs["region_name"] = region_name

    return series