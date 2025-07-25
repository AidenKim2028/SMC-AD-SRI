# SRI python

Calculates SRI, sleep median time, average hourly sleep time from given actigraphy csv (exported from Philips Actiwatch software) 
This has option for visualizing the actigraphy data for CNN analysis.

# Feature Analysis 

main.py --- calls csv_read.py, patient_data.py, matlab_data.py (when requested), exports csv from parsed data
csv_read.py --- parses data from actigraphy csv
patient_data.py --- validates the data, calculates SRI, sleep median time, average hourly sleep time from the data

## Sleep Regularity Index (SRI) 
- The probability of an individual being in the same state (asleep or awake) at any two time points 24 h apart

## Sleep median time
- Calculated from epochs counted as sleep time

## Average hourly sleep time
- Hourly sleep time counted daily then averaged 
