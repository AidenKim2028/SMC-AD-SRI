import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import math
import statistics
from scipy.signal import find_peaks

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
            if self.spo2[i0:i1] >= self.lower: 
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
        self.step1_define_events()
        self.step2_exclude_artifacts()
        self.step3_calc_area_and_weight()
        self.step4_calc_normalization()
        return self.step5_compute_whi()
class PSG(object):
    def __init__(self, PSG_no, total_sleep_time, SpO2_path, Events_path):
        self.PSG_no = PSG_no
        self.total_sleep_time = total_sleep_time
        self.SpO2_path = SpO2_path

    def get_SpO2(self): #SpO2 불러오기
        SpO2 = pd.read_csv(self.SpO2_path, sep = '\t', header = 1).rename(columns = {'Trace Name: SpO2': 'SpO2','Trace Name: Sp02': 'SpO2'})
        SpO2.index.name = 'Time'

        if len(SpO2) == 0:
            self.SpO2 = SpO2
            return

        SpO2.reset_index(level=0, inplace=True)
        SpO2.Time = SpO2.Time.apply(lambda x: x[:-2] + '0' + x[-2:] if len(x) == 11 else x)
        SpO2.Time = SpO2.Time.apply(lambda x: x[:-1] + '00' + x[-1] if len(x) == 10 else x)
        SpO2['temp_Time'] = SpO2.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S:%f'))
        midnight = SpO2.temp_Time.idxmin()

        if midnight == 0:
            if SpO2.temp_Time.loc[midnight] < datetime.strptime('12:00:00', '%H:%M:%S'):
                SpO2.Time = SpO2.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S:%f') + timedelta(days = 1))
            else:
                SpO2.Time = SpO2.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S:%f'))
        else:
            SpO2_before_midnight = SpO2.loc[:midnight - 1]
            SpO2_after_midnight = SpO2.loc[midnight:]
            SpO2_before_midnight.Time = SpO2_before_midnight.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S:%f'))
            SpO2_after_midnight.Time = SpO2_after_midnight.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S:%f') + timedelta(days = 1))
            SpO2 = pd.concat([SpO2_before_midnight, SpO2_after_midnight])

        SpO2.SpO2 = SpO2.SpO2.astype(float)
        SpO2 = SpO2.sort_values(by = ['Time']).reset_index(drop = True)
        
        abnormal_SpO2_index_list = SpO2.loc[SpO2.SpO2 < 60].index
        
        for index in abnormal_SpO2_index_list: #SpO2 60 미만은 모두 그 전 SpO2 것으로 imputation
            if index == 0:
                continue
            SpO2.loc[index, 'SpO2'] = SpO2.loc[index - 1, 'SpO2']
        
        self.SpO2 = SpO2.set_index('Time')
    