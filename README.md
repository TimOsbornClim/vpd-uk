# vpd-uk

Analysis of vapour pressure deficit for the UK.

Uses multiple observational datasets (CRU-TS, HadUK-Grid, ERA5) to create monthly timeseries of vapour pressure deficit (VPD) for different locations or regions within the UK. Dataset can be compared and plotted on the same figures.

The most complete figures (created by `pl-cru-had-era.py`) show a seasonal-average timeseries of VPD (the user can choose the season) for the region or grid cell chosen, for all three datasets, and a smoothed series is also shown based on the multi-dataset mean. For the multi-dataset mean to be useful, it is important that the three datasets are compatible. To help achieve this, the CRU-TS and ERA5 timeseries are linearly transformed so thay their mean and standard deviations match those of HadUK-Grid over their common period. HadUK-Grid is chosen as the target for this transformation because it is based on the greatest amount of in situ observed data, so it is likely to be the most reliable VPD series.




