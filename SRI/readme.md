# SRI python

Calculates SRI, sleep median time, average hourly sleep time from given actigraphy csv (exported from Philips Actiwatch software), per article by AJK Philips et al. (https://doi.org/10.1038/s41598-017-03171-4)

This has an option for visualizing the actigraphy data for CNN analysis.

# Feature Analysis 

main.py --- calls csv_read.py, patient_data.py, matlab_data.py (when requested), exports csv from the calculated data

csv_read.py --- parses data from Actigraphy csv

patient_data.py --- validates the data (>5 days, >22 hours per day), calculates SRI, sleep median time, average hourly sleep time from the data

## Sleep Regularity Index (SRI) 
- The probability of an individual being in the same state (asleep or awake) at any two time points 24 h apart

## Sleep median time
- Calculated from epochs counted as sleep time

## Average hourly sleep time
- Hourly sleep time counted daily then averaged 
