#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 09:07:53 2026

@author: f055
"""


"""
Utilities for analysing climate data.
"""

import pandas as pd



def seasonal_mean(series, months):
    """
    Calculate seasonal means from a monthly time series.

    Parameters
    ----------
    series : pandas.Series
        Monthly time series with datetime index.

    months : list
        List of month numbers, e.g.

            [3,4,5,6]     # Mar-Jun
            [12,1,2]      # DJF
            [12,1,2,3,4]  # Dec-Apr

    Returns
    -------
    pandas.Series
        Seasonal means indexed by season year.
        
   Notes
   -----
   For seasons crossing a year boundary, the season is assigned
   to the year containing January.

   Example:
       Dec 2000 - Apr 2001  -> season year 2001
       Dec 2001 - Apr 2002  -> season year 2002
    """

    df = series.to_frame("value")

    df["year"] = df.index.year
    df["month"] = df.index.month

    # Detect whether season crosses year boundary

    crosses_year = any(
        months[i] > months[i + 1]
        for i in range(len(months) - 1)
    )

    df["season_year"] = df["year"]

    if crosses_year:

        months_in_previous_year = [
            m for m in months
            if m >= months[0]
        ]

        df.loc[
            df["month"].isin(months_in_previous_year),
            "season_year"
        ] += 1

    # Keep only desired months

    df = df[df["month"].isin(months)]

    # Require complete seasons

    seasonal = (
        df.groupby("season_year")
          .filter(lambda x: len(x) == len(months))
          .groupby("season_year")["value"]
          .mean()
    )

    return seasonal


