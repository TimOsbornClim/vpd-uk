#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 21:24:11 2026

@author: f055
"""


"""
Example script to download ERA5 temperature and dewpoint temperature
for a single grid cell using the CDS API
"""

from era5_functions import download_era5_monthly


era5_path = "/Users/f055/Documents/data/ERA5/"

lat = 52.75
lon = 1.25

syr = 2026
eyr = 2026

outfile = (
    f"era5_monthly_t2m_d2m_"
    f"lat{lat:.2f}_lon{lon:.2f}_"
    f"{syr}01-{eyr}12.nc"
)

era5_file = era5_path + outfile



download_era5_monthly(
    lat=lat,
    lon=lon,
    outfile=era5_file,
    start_year=syr,
    end_year=eyr,
)



