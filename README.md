# SRI Project Overview 
Study goal: Effect of Lecanemab on Alzheimer Patients' Sleep Regularity.
1. Build a program that calculates Sleep Regularity Index (SRI) with the input of time (epoch: 30 or 60sec) and Sleep status (sleep/wake).
2. Analyze the correlation between patients' SRI, baseline demographic, PSG, Neuropsychological data. 
3. Compare the SRI of the patients before and after the usage of Lecanemab. 
   
# Weighted Hypoxemia Index (WHI) & Hypoxic Burden Calculator

This repository provides Python scripts for calculating:

- **Apnea-specific hypoxic burden** (%·min/h)
- **Hypopnea-specific hypoxic burden** (%·min/h)
- **Total hypoxic burden** (%·min/h)
- **Weighted Hypoxemia Index (WHI)** (%·min²/hour
- 
The calculations are based on **SpO₂ time-series data** and **respiratory event annotations** from polysomnography (PSG).
---

## Overview

- **Hypoxic Burden** measures the total depth × duration of all desaturation events across the night, normalized per hour of sleep.
- **Weighted Hypoxemia Index (WHI)** goes further by weighting each event's area (Δᵢ) by its duration (Φᵢ), and scaling by the fraction of the night spent below a specified saturation threshold (Ω).

**Formula:**
\[
\mathrm{WHI} = \Omega \times \frac{\sum_{i} \left( \Delta_i \times \Phi_i \right)}{\mathrm{TST\ (hours)}}
\]

Where:
- **Δᵢ**: Area under the desaturation curve for event *i* (fractional drop × minutes)
- **Φᵢ**: Duration of event *i* (minutes)
- **Ω**: Fraction of total sleep time spent below `upper_thr` (unitless)
- **TST**: Total sleep time in hours

**WHI Units:** `%·min²/hour`

---

## Repository Structure

### `hypoxic_burden.py`
- Loads SpO₂ waveform data (`get_SpO2`) and respiratory event data (`get_Events`).
- Classifies events into apnea and hypopnea.
- Aligns and averages SpO₂ around events.
- Defines search windows for hypoxic burden.
- Calculates:
  - Apnea-specific hypoxic burden
  - Hypopnea-specific hypoxic burden
  - Total hypoxic burden

**Output Units:** `%·min/h`

---

### `WHI.py`
- **`WeightedHypoxemiaIndex` class:**
  - Filters raw SpO₂ data.
  - Detects desaturation events (`step1_define_events`) with:
    - Merging of short recoveries (`gap_merge_sec`)
    - Ignoring brief dips (`min_event_dur_sec`)
    - Splitting very long events (`max_event_dur_sec`)
  - Excludes artifacts below `lower_thr`.
  - Calculates:
    - **Δᵢ** in fractional minutes
    - **Φᵢ** in minutes
  - Computes Ω as fraction of the night < `upper_thr`.
  - Outputs WHI in `%·min²/hour`.

- **`PSG` class (inherits from hypoxic_burden.PSG):**
  - Adds `calculate_whi()` method for convenience.

---

### `calculate_weighted_hypoxemia.ipynb`
- Example batch-processing notebook.
- Requires:
  - **SpO₂ files** (`.txt`)
  - **Event files** (`.txt`)
  - **Report files** (`.pdf` with total sleep time)
- Produces Excel summary with all metrics.

---

## 📁 Input File Naming

- **SpO₂ files**: `PSG_no,...` (comma after PSG_no)
- **Event files**: `... PSG_no-...` (space + dash after PSG_no)
- **Report files**: `PSG_no-...`

---

## ▶️Usage

1. Place your data in:
e.g.
Raw_data/6-SpO2/
Raw_data/6-Events/
Raw_data/6-Reports/

2. Adjust paths in `calculate_weighted_hypoxemia.ipynb`:
```python
SpO2_folder_path = '.../6-SpO2/'
Events_folder_path = '.../6-Events/'
Reports_folder_path = '.../6-Reports/'
Result_path = '.../'
Result_name = 'Weighted_hypoxemia_6'

3. Run the notebook.
Output: Weighted_hypoxemia_6.xlsx
