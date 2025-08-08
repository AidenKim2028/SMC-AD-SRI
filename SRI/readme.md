# SRI python

Calculates SRI, sleep median time, average hourly sleep time from given actigraphy csv (exported from Philips Actiwatch software), per article by AJK Philips et al. (https://doi.org/10.1038/s41598-017-03171-4)

This has an option for visualizing the actigraphy data for CNN analysis.

# Feature Analysis 

main.py --- calls csv_read.py, patient_data.py, matlab_data.py (when requested), exports csv from the calculated data

csv_read.py --- parses data from Actigraphy csv. 

patient_data.py --- validates the data (>5 days, >22 hours per day), calculates SRI, total sleep time, sleep median time, sleep time in day, sleep time in night, and average hourly sleep time from the data

## Sleep Regularity Index (SRI) 
- The probability of an individual being in the same state (asleep or awake) at any two time points 24 h apart
- Given N days of recording divided to M epochs, suppose $s_{i,j} = 1$ if the patient is sleeping on the epoch j in day i and $s_{i,j} = 0$ if the patient is awake

```math
-100 + \frac{200}{M(N-1)} \sum_{j=1}^{M} \sum_{i=1}^{N-1} \delta(s_{i,j}, s_{i+1,j})
```

- Whereas $\delta(s_{i,j},s_{i+1,j}) = 1$ if $s_{i,j}=s_{i+1,j}$ and 0 otherwise.

## Sleep median time
- Calculated from epochs counted as sleep time, per article by Lunsford-Avery et al. (https://doi.org/10.1038/s41598-018-32402-5)
- A mean of circular quantities, t = time of day in seconds at epoch j

```math
 \frac{86400}{2\pi} \mathrm{arctan2} \left( \sum^{M}_{j=1} \sum^{N}_{i=1} {s_{i, j}} {\mathrm{sin} \frac{2\pi t_i}{86400}} + \sum^{M}_{j=1} \sum^{N}_{i=1} {s_{i, j}} {\mathrm{cos} \frac{2\pi t_i}{86400}} \right)
```

## Total sleep time (TST)
- Calculated by counting epochs recorded as sleeping
- TST at daytime is the TST counted on 10 AM to 10 PM.
- TST at nighttime is the TST counted on 10 PM to 10 AM.

## Average hourly sleep time
- Hourly sleep time counted daily then averaged 
