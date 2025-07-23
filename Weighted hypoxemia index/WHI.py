import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import math
import statistics
from scipy.signal import find_peaks
import hypoxic_burden

class WeightedHypoxemiaIndex:
    def __init__(self, spo2: np.ndarray, time: np.ndarray,
                 upper_thr: float = 90.0, lower_thr: float = 50.0):
        self.spo2 = spo2
        self.time = time
        self.upper = upper_thr
        self.lower = lower_thr
        self.events = []        # will hold (start_idx, end_idx)
        self.filtered = []      # after artifact exclusion
        self.delta = []         # area Δᵢ per event
        self.phi   = []         # weighted factor Φᵢ per event
        self.omega = 0.0        # normalization Ω

    def filter_data(self):
        valid = np.isfinite(self.spo2) & (self.spo2 > 0)

        spo2_clean = self.spo2[valid]
        time_clean = self.time[valid]
        if time_clean.size > 0:
            time_rebased = time_clean - time_clean[0]
        else:
            time_rebased = time_clean
        self.spo2 = spo2_clean
        self.time = time_rebased

    def step1_define_events(self):  # Detect resaturation events crossing the upper threshold 
        is_above = True 
        start_i = None 
        for i in range(len(self.spo2)): 
            if is_above and self.spo2[i] < self.upper:
                start_i = i
                is_above = False 
            elif not is_above and self.spo2[i] >= self.upper: 
                self.events.append((start_i, i))
                is_above = True 
    
    def step2_exclude_artifacts(self):  # Remove any event dipping below the lower threshold
        for (i0, i1) in self.events:
            segment = self.spo2[i0:i1]
            if np.all(segment >= self.lower): 
                self.filtered.append((i0, i1))

    def step3_calc_area_and_weight(self): # For each filtered event compute Δᵢ (area under upper_thr) and Φᵢ (event duration)
        for (i0, i1) in self.filtered:
            s = self.spo2[i0:i1]
            t = self.time[i0:i1]
            drops = np.clip(self.upper - s, 0, None) # area below upper threshold (Δᵢ) via trapezoid
            delta_i = np.trapz(drops, t)
            phi_i = t[-1] - t[0] # linear weighted factor 
            self.delta.append(delta_i)
            self.phi.append(phi_i)

    def step4_calc_normalization(self): #Ω = TST90c / TSTc
        TSTc = self.time[-1] - self.time[0]
        below = self.spo2 < self.upper
        TST90c = below.sum() # TST90c = total seconds spent below upper threshold
        if TSTc > 0: 
            self.omega = TST90c / TSTc
        else: 
            self.omega = 0; 

    def step5_compute_whi(self) -> float:
        weighted_sum = sum(d * p for d, p in zip(self.delta, self.phi))
        return self.omega * weighted_sum

    def weighted_hypoxemia(self) -> float:  # Run all five steps and return WHI
        self.filter_data()
        self.step1_define_events()
        self.step2_exclude_artifacts()
        self.step3_calc_area_and_weight()
        self.step4_calc_normalization()
        return self.step5_compute_whi()

from hypoxic_burden import PSG as BasePSG

class PSG(BasePSG):
    def calculate_whi(self, upper_thr: float = 90.0, lower_thr: float = 50.0):
        # Ensure SpO₂ data is loaded
        if not hasattr(self, 'SpO2'):
            self.get_SpO2()
        # Convert timestamp index to elapsed seconds
        spo2_df = self.SpO2.copy()
        times = (spo2_df.index - spo2_df.index[0]).total_seconds().to_numpy()
        values = spo2_df['SpO2'].to_numpy()
        # Compute and return WHI
        whi_calc = WeightedHypoxemiaIndex(values, times, upper_thr, lower_thr)

        # print number of spo2 below upper limit 
        print(f"{self.PSG_no}: {int(np.sum(values < 90.0))} times down {whi_calc.upper}")

        return whi_calc.weighted_hypoxemia()

