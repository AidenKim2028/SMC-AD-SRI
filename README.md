# Project Overview 
Study goal: Effect of Lecanemab on Alzheimer Patients' Sleep Regularity.
1. Build a program that calculates Sleep Regularity Index (SRI) with the input of time (epoch: 30 or 60sec) and Sleep status (sleep/wake).
2. Analyze the correlation between patients' SRI, baseline demographic, PSG, Neuropsychological data. 
3. Compare the SRI of the patients before and after the usage of Lecanemab. 
   
# Feature Analysis 

## Sleep Regularity Index (SRI) 
- The probability of an individual being in the same state (asleep or awake) at any two time points 24 h apart

# Weighted Hypoxemia Index (WHI)

Following description is a five‐step procedure used to compute the **Weighted Hypoxemia Index (WHI)** from a continuous SpO₂ recording.

---

### 1. Event Detection  
Scan the SpO₂ time series to identify individual desaturation events relative to an **upper threshold** (e.g. 90 %):
- **Start**: when SpO₂ falls below the upper threshold  
- **End**: when SpO₂ rises back above the upper threshold  
- **Output**: a list of (start_idx, end_idx) pairs marking each candidate event

---

### 2. Artifact Exclusion  
Discard any candidate event that appears physiologically implausible by applying a **lower threshold** (e.g. 50 %):
- For each event window, check the minimum SpO₂  
- **Keep** the event only if every sample ≥ lower threshold  
- **Result**: a filtered list of bona fide desaturation events

---

### 3. Compute Per‑Event Area and Weight  
For each retained event:
1. **Depth curve (Δᵢ)**  
   - At each timepoint, compute `drop = max(upper_thr – SpO₂, 0)`  
   - Integrate (`trapezoidal rule`) over the event duration → Δᵢ (percent·seconds)
2. **Duration weight (Φᵢ)**  
   - Compute event length in seconds (`end_time – start_time`) → Φᵢ  

---

### 4. Compute Normalization Factor (Ω)  
Scale by the fraction of time spent below the upper threshold:  
- **TST₍upper₎** = total seconds where SpO₂ < upper threshold  
- **TST₍total₎** = total recording duration in seconds  

\[
\Omega = `TST_upper / TST_total`
\]

---

### 5. Aggregate into WHI  
Combine depth, duration, and prevalence into a single scalar:  
- **WHI** = `Ω * sum(Δ_i * Φ_i for all events i)`  
  - **Units:** (percent·seconds²), often normalized per hour  
  - **Interpretation:**  
    - Ω captures *how often* desaturations occur  
    - Δᵢ × Φᵢ captures *how deep* and *how long* each event is  
    - WHI unifies these into one index for clinical or research use  

---

**The Code** can be found in [`WHI.py`](./Weighted%20hypoxemia%20index/WHI.py) and [`Calculate_weighted_hypoxemia.ipynb`](./Weighted%20hypoxemia%20index/Calculate_weighted_hypoxemia.ipynb)

## RBDtector
- An open-source software designed to detect REM Sleep Without Atonia (RSWA)— a key diagnostic marker of REM Sleep Behavior Disorder (RBD).   
- A Python-based tool that analyzes raw polysomnography (PSG) data, especially electromyography (EMG) channels, to automatically identify muscle activity during REM sleep. It's built around the established SINBAR visual scoring criteria, covering tonic, phasic, and any EMG activity types. 

## Polysomnography (PSG) 

## Baseline Demographics, Neuropsychological Data
