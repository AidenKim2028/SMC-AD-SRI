import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import math
import statistics
from scipy.signal import find_peaks

def mean(any_list):
    if len(any_list) == 0:
        return 0
    else:
        return statistics.mean(any_list)

class resp_event(object): #class of respriatory event
    def __init__(self, resp_event_index, start, end, dur):
        self.resp_event_index = resp_event_index
        self.start = start
        self.end = end
        self.dur = dur

    def set_baseline_SpO2(self, SpO2): #maximum SpO2 during 100 seconds pre from the end of respiratory event
        end = self.end
        try:
            self.baseline_SpO2 = max(SpO2.loc[end - timedelta(seconds = 100):end].SpO2) 
        except:
            self.baseline_SpO2 = 0

    def set_SpO2_pre_post_from_event_end(self, SpO2): #SpO2 during maximum desaturation duration seconds pre and post from the end of respiratory event
        end = self.end
        self.SpO2_pre_post_from_event_end = SpO2.loc[end - timedelta(seconds = 100):end + timedelta(seconds = 100)] 
    
    def shift_SpO2_by_end_time(self): #Shift SpO2 by end time of respiratory event
        SpO2_shifted_by_time = self.SpO2_pre_post_from_event_end.copy()
        SpO2_shifted_by_time.index = SpO2_shifted_by_time.index.map(lambda x: (x - self.end).total_seconds())
        self.SpO2_shifted_by_time = SpO2_shifted_by_time

    def preprocessing(self, SpO2): #3 process over (set_baseline_SpO2, set_SpO2_pre_post_from_event_end, shift_SpO2_by_end_time)
        self.set_baseline_SpO2(SpO2)
        self.set_SpO2_pre_post_from_event_end(SpO2)
        self.shift_SpO2_by_end_time()

    def set_SpO2_by_search_window(self, search_window_start, search_window_end): #set SpO2 during search window
        self.SpO2_by_search_window = self.SpO2_shifted_by_time.loc[search_window_start:search_window_end]


class PSG(object):
    def __init__(self, PSG_no, total_sleep_time, SpO2_path, Events_path):
        self.PSG_no = PSG_no
        self.total_sleep_time = total_sleep_time
        self.SpO2_path = SpO2_path
        self.Events_path = Events_path

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

    def get_Events(self): #Events 불러오기
        try:
            Events = pd.read_csv(self.Events_path, sep = '\t', header = 20, encoding = 'CP949').rename(columns = {'Time [hh:mm:ss]': 'Time', 'Duration[s]': 'Duration'})
            Events['temp_Time'] = Events.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S'))
        except:
            Events = pd.read_csv(self.Events_path, sep = '\t', header = 17, encoding = 'CP949').rename(columns = {'Time [hh:mm:ss]': 'Time', 'Duration[s]': 'Duration'})
            Events['temp_Time'] = Events.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S'))

        Events = Events.loc[Events.Event.apply(lambda x: 'pnea' in x.lower())]
        
        if len(Events)==0:
            self.Events = Events
            return
        
        midnight = Events['temp_Time'].idxmin()
        if midnight == min(Events.index):
            if Events.temp_Time.loc[midnight] < datetime.strptime('12:00:00', '%H:%M:%S'):
                Events.Time = Events.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S') + timedelta(days = 1))
            else:
                Events.Time = Events.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S'))
        else:
            Events_before_midnight = Events.loc[:midnight - 1]
            Events_after_midnight = Events.loc[midnight:]
            Events_before_midnight.Time = Events_before_midnight.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S'))
            Events_after_midnight.Time = Events_after_midnight.Time.apply(lambda x: datetime.strptime(x, '%H:%M:%S') + timedelta(days = 1))
            Events = pd.concat([Events_before_midnight, Events_after_midnight])
        Events = Events.assign(start = Events.Time, end = Events.Time + Events.Duration.apply(lambda x: timedelta(seconds = x)))

        Events.sort_values(by='Duration', ascending=False)
        if len(Events[Events.start.duplicated()]) > 0:
            Events = Events.drop(Events[Events.start.duplicated()].index)

        self.Events = Events.set_index('Time').sort_index()
        return

    def classify_Events(self): #Events (apnea, hypopnea, desat) 으로 나누기
        Events = self.Events
        Events_apnea = Events.loc[Events.Event.apply(lambda x: 'apnea' in x.lower())]
        Events_apnea = Events_apnea.assign(apnea_index = range(len(Events_apnea)))
        Events_hypopnea = Events.loc[Events.Event.apply(lambda x: 'hypopnea' in x.lower())]
        Events_hypopnea = Events_hypopnea.assign(hypopnea_index = range(len(Events_hypopnea)))

        self.Events_apnea = Events_apnea
        self.mean_apnea_dur = mean(Events_apnea.Duration)
        self.Events_hypopnea = Events_hypopnea
        self.mean_hypopnea_dur = mean(Events_hypopnea.Duration)

    def generate_resp_event_dic(self): #make apnea, hypopnea dictionary (index -> respiratory event class), set baseline SpO2, shift SpO2 by end time
        apnea_dic = {}
        for event_time in self.Events_apnea.index:
            event = self.Events_apnea.loc[event_time]
            apnea_index = event.apnea_index
            apnea_dic[apnea_index] = resp_event(apnea_index, event.start, event.end, event.Duration)
            apnea_dic[apnea_index].preprocessing(self.SpO2)

        hypopnea_dic = {}
        for event_time in self.Events_hypopnea.index:
            event = self.Events_hypopnea.loc[event_time]
            hypopnea_index = event.hypopnea_index
            hypopnea_dic[hypopnea_index] = resp_event(hypopnea_index, event.start, event.end, event.Duration)
            hypopnea_dic[hypopnea_index].preprocessing(self.SpO2)

        self.apnea_dic = apnea_dic
        self.hypopnea_dic = hypopnea_dic

    def overlap_SpO2_of_resp_events(self): #collect and overlap all SpO2 curve of respiratory events regardless of  desaturation event
        total_SpO2_during_apnea = pd.DataFrame(columns = ['SpO2'])
        total_SpO2_during_hypopnea = pd.DataFrame(columns = ['SpO2'])
        total_SpO2_during_resp_event = pd.DataFrame(columns = ['SpO2'])

        for resp_event_index in self.apnea_dic:
            resp_event = self.apnea_dic[resp_event_index]
            SpO2_shifted_by_time = resp_event.SpO2_shifted_by_time
            total_SpO2_during_apnea = total_SpO2_during_apnea.append(SpO2_shifted_by_time)
            total_SpO2_during_resp_event = total_SpO2_during_resp_event.append(SpO2_shifted_by_time)

        for resp_event_index in self.hypopnea_dic:
            resp_event = self.hypopnea_dic[resp_event_index]
            SpO2_shifted_by_time = resp_event.SpO2_shifted_by_time
            total_SpO2_during_hypopnea = total_SpO2_during_hypopnea.append(SpO2_shifted_by_time)
            total_SpO2_during_resp_event = total_SpO2_during_resp_event.append(SpO2_shifted_by_time)

        total_SpO2_during_apnea.index = total_SpO2_during_apnea.index.map(lambda x: math.floor(x*2)/2)
        total_SpO2_during_hypopnea.index = total_SpO2_during_hypopnea.index.map(lambda x: math.floor(x*2)/2)
        total_SpO2_during_resp_event.index = total_SpO2_during_resp_event.index.map(lambda x: math.floor(x*2)/2)

        self.total_SpO2_during_apnea = total_SpO2_during_apnea
        self.total_SpO2_during_hypopnea = total_SpO2_during_hypopnea
        self.total_SpO2_during_resp_event = total_SpO2_during_resp_event

    def plot_overlap_SpO2_of_resp_events(self): #plot individual shifted SpO2 of respiratory events regardless of desaturation
        plt.figure(figsize=(8,5))

        for resp_event_index in self.apnea_dic:
            resp_event = self.apnea_dic[resp_event_index]
            SpO2_shifted_by_time = resp_event.SpO2_shifted_by_time
            plt.plot(SpO2_shifted_by_time.index, SpO2_shifted_by_time.SpO2, color = 'm', alpha = 0.2) #plot time-shifted desaturation curve caused by apnea

        plt.plot([],[], color = 'm', label = 'Apnea (n=%d)'%(len(self.apnea_dic)))

        for resp_event_index in self.hypopnea_dic:
            resp_event = self.hypopnea_dic[resp_event_index]
            SpO2_shifted_by_time = resp_event.SpO2_shifted_by_time
            plt.plot(SpO2_shifted_by_time.index, SpO2_shifted_by_time.SpO2, color = 'y', alpha = 0.2) #plot time-shifted desaturation curve caused by hypopnea

        plt.plot([],[], color = 'y', label = 'Hypopnea (n=%d)'%(len(self.hypopnea_dic)))

        plt.title('Overlapped SpO2 curves of respiratory events')
        plt.xlabel('Time (s)')
        plt.ylabel('SpO2 (%)')
        plt.ylim(55, 100)
        plt.legend(loc = 'lower left')

        plt.show()

    def average_SpO2_of_resp_events(self): #average of SpO2 during respiratory events
        average_SpO2_during_apnea = pd.DataFrame(columns = ['SpO2'])
        timeline_apnea = self.total_SpO2_during_apnea.index

        if len(timeline_apnea) > 0:
            for i in range(int(min(timeline_apnea)*2), int(max(timeline_apnea)*2) + 1):
                try:
                    time_specific_SpO2 = self.total_SpO2_during_apnea.loc[i/2]
                    if time_specific_SpO2.shape[0] == 0:
                        average_SpO2_value = pd.DataFrame([average_SpO2_during_apnea.loc[(i-1)/2, 'SpO2']], columns = ['SpO2'], index = [i/2])
                    elif isinstance(time_specific_SpO2.SpO2, float):
                        average_SpO2_value = pd.DataFrame([time_specific_SpO2.SpO2], columns = ['SpO2'], index = [i/2])
                    else:
                        average_SpO2_value = pd.DataFrame([np.mean(time_specific_SpO2.SpO2)], columns = ['SpO2'], index = [i/2])
                except:
                    average_SpO2_value = pd.DataFrame([average_SpO2_during_apnea.loc[(i-1)/2, 'SpO2']], columns = ['SpO2'], index = [i/2])
                average_SpO2_during_apnea = average_SpO2_during_apnea.append(average_SpO2_value)

        average_SpO2_during_hypopnea = pd.DataFrame(columns = ['SpO2'])
        timeline_hypopnea = self.total_SpO2_during_hypopnea.index

        if len(timeline_hypopnea) > 0:
            for i in range(int(min(timeline_hypopnea)*2), int(max(timeline_hypopnea)*2) + 1):
                try:
                    time_specific_SpO2 = self.total_SpO2_during_hypopnea.loc[i/2]
                    if time_specific_SpO2.shape[0] == 0:
                        average_SpO2_value = pd.DataFrame([average_SpO2_during_hypopnea.loc[(i-1)/2, 'SpO2']], columns = ['SpO2'], index = [i/2])
                    elif isinstance(time_specific_SpO2.SpO2, float):
                        average_SpO2_value = pd.DataFrame([time_specific_SpO2.SpO2], columns = ['SpO2'], index = [i/2])
                    else:
                        average_SpO2_value = pd.DataFrame([np.mean(time_specific_SpO2.SpO2)], columns = ['SpO2'], index = [i/2])
                except:
                    average_SpO2_value = pd.DataFrame([average_SpO2_during_hypopnea.loc[(i-1)/2, 'SpO2']], columns = ['SpO2'], index = [i/2])
                average_SpO2_during_hypopnea = average_SpO2_during_hypopnea.append(average_SpO2_value)

        average_SpO2_during_resp_event = pd.DataFrame(columns = ['SpO2'])
        timeline_resp_event = self.total_SpO2_during_resp_event.index

        if len(timeline_resp_event) > 0:
            for i in range(int(min(timeline_resp_event)*2), int(max(timeline_resp_event)*2) + 1):
                try:
                    time_specific_SpO2 = self.total_SpO2_during_resp_event.loc[i/2]
                    if time_specific_SpO2.shape[0] == 0:
                        average_SpO2_value = pd.DataFrame([average_SpO2_during_resp_event.loc[(i-1)/2, 'SpO2']], columns = ['SpO2'], index = [i/2])
                    elif isinstance(time_specific_SpO2.SpO2, float):
                        average_SpO2_value = pd.DataFrame([time_specific_SpO2.SpO2], columns = ['SpO2'], index = [i/2])
                    else:
                        average_SpO2_value = pd.DataFrame([np.mean(time_specific_SpO2.SpO2)], columns = ['SpO2'], index = [i/2])
                except:
                    average_SpO2_value = pd.DataFrame([average_SpO2_during_resp_event.loc[(i-1)/2, 'SpO2']], columns = ['SpO2'], index = [i/2])
                average_SpO2_during_resp_event = average_SpO2_during_resp_event.append(average_SpO2_value)

        self.average_SpO2_during_apnea = average_SpO2_during_apnea
        self.average_SpO2_during_hypopnea = average_SpO2_during_hypopnea
        self.average_SpO2_during_resp_event = average_SpO2_during_resp_event

    def set_search_window_apnea(self): #find peak points of overlapped SpO2 and define as search window
        average_SpO2_during_apnea = self.average_SpO2_during_apnea

        if len(self.average_SpO2_during_apnea) == 0:
            self.search_window_apnea_start = 0
            self.search_window_apnea_end = 0
            return

        average_resp_event_peaks, _ = find_peaks(average_SpO2_during_apnea.SpO2, prominence=0.5)#, width=1)
        average_resp_event_peak_times = average_SpO2_during_apnea.iloc[average_resp_event_peaks].index
        average_resp_event_low_peaks, _ = find_peaks(np.array(-1) * average_SpO2_during_apnea.SpO2, prominence=0.5)#, width=1)
        average_resp_event_low_peak_times = average_SpO2_during_apnea.iloc[average_resp_event_low_peaks].index

        try:
            average_resp_event_low_peak_time = min([time for time in average_resp_event_low_peak_times if time > 0])
        except:
            average_resp_event_low_peak_time = 0

        pre_desat_time_list = [time for time in average_resp_event_peak_times if time < average_resp_event_low_peak_time]
        post_desat_time_list = [time for time in average_resp_event_peak_times if time > average_resp_event_low_peak_time]

        if len(pre_desat_time_list) == 0:
            pre_desat_SpO2 = average_SpO2_during_apnea.loc[average_resp_event_low_peak_time - 50:average_resp_event_low_peak_time]
            max_pre_desat_SpO2 = max(pre_desat_SpO2.SpO2)
            search_window_start = max(pre_desat_SpO2.loc[pre_desat_SpO2.SpO2 == max_pre_desat_SpO2].index)
        else:
            search_window_start = max(pre_desat_time_list)
        
        if len(post_desat_time_list) == 0:
            post_desat_SpO2 = average_SpO2_during_apnea.loc[average_resp_event_low_peak_time:average_resp_event_low_peak_time + 50]
            max_post_desat_SpO2 = max(post_desat_SpO2.SpO2)
            search_window_end = min(post_desat_SpO2.loc[post_desat_SpO2.SpO2 == max_post_desat_SpO2].index)
        else:
            search_window_end = min(post_desat_time_list)

        self.search_window_apnea_start = search_window_start
        self.search_window_apnea_end = search_window_end

    def set_search_window_hypopnea(self): #find peak points of overlapped SpO2 and define as search window
        average_SpO2_during_hypopnea = self.average_SpO2_during_hypopnea

        if len(self.average_SpO2_during_hypopnea) == 0:
            self.search_window_hypopnea_start = 0
            self.search_window_hypopnea_end = 0
            return

        average_resp_event_peaks, _ = find_peaks(average_SpO2_during_hypopnea.SpO2, prominence=0.5)#, width=1)
        average_resp_event_peak_times = average_SpO2_during_hypopnea.iloc[average_resp_event_peaks].index
        average_resp_event_low_peaks, _ = find_peaks(np.array(-1) * average_SpO2_during_hypopnea.SpO2, prominence=0.5)#, width=1)
        average_resp_event_low_peak_times = average_SpO2_during_hypopnea.iloc[average_resp_event_low_peaks].index

        try:
            average_resp_event_low_peak_time = min([time for time in average_resp_event_low_peak_times if time > 0])
        except:
            average_resp_event_low_peak_time = 0

        pre_desat_time_list = [time for time in average_resp_event_peak_times if time < average_resp_event_low_peak_time]
        post_desat_time_list = [time for time in average_resp_event_peak_times if time > average_resp_event_low_peak_time]

        if len(pre_desat_time_list) == 0:
            pre_desat_SpO2 = average_SpO2_during_hypopnea.loc[average_resp_event_low_peak_time - 50:average_resp_event_low_peak_time]
            max_pre_desat_SpO2 = max(pre_desat_SpO2.SpO2)
            search_window_start = max(pre_desat_SpO2.loc[pre_desat_SpO2.SpO2 == max_pre_desat_SpO2].index)
        else:
            search_window_start = max(pre_desat_time_list)
        
        if len(post_desat_time_list) == 0:
            post_desat_SpO2 = average_SpO2_during_hypopnea.loc[average_resp_event_low_peak_time:average_resp_event_low_peak_time + 50]
            max_post_desat_SpO2 = max(post_desat_SpO2.SpO2)
            search_window_end = min(post_desat_SpO2.loc[post_desat_SpO2.SpO2 == max_post_desat_SpO2].index)
        else:
            search_window_end = min(post_desat_time_list)

        self.search_window_hypopnea_start = search_window_start
        self.search_window_hypopnea_end = search_window_end

    def set_search_window_resp_event(self): #find peak points of overlapped SpO2 and define as search window
        average_SpO2_during_resp_event = self.average_SpO2_during_resp_event

        if len(self.average_SpO2_during_resp_event) == 0:
            self.search_window_resp_event_start = 0
            self.search_window_resp_event_end = 0
            return

        average_resp_event_peaks, _ = find_peaks(average_SpO2_during_resp_event.SpO2, prominence=0.5)#, width=1)
        average_resp_event_peak_times = average_SpO2_during_resp_event.iloc[average_resp_event_peaks].index
        average_resp_event_low_peaks, _ = find_peaks(np.array(-1) * average_SpO2_during_resp_event.SpO2, prominence=0.5)#, width=1)
        average_resp_event_low_peak_times = average_SpO2_during_resp_event.iloc[average_resp_event_low_peaks].index

        try:
            average_resp_event_low_peak_time = min([time for time in average_resp_event_low_peak_times if time > 0])
        except:
            average_resp_event_low_peak_time = 0

        pre_desat_time_list = [time for time in average_resp_event_peak_times if time < average_resp_event_low_peak_time]
        post_desat_time_list = [time for time in average_resp_event_peak_times if time > average_resp_event_low_peak_time]

        if len(pre_desat_time_list) == 0:
            pre_desat_SpO2 = average_SpO2_during_resp_event.loc[average_resp_event_low_peak_time - 50:average_resp_event_low_peak_time]
            max_pre_desat_SpO2 = max(pre_desat_SpO2.SpO2)
            search_window_start = max(pre_desat_SpO2.loc[pre_desat_SpO2.SpO2 == max_pre_desat_SpO2].index)
        else:
            search_window_start = max(pre_desat_time_list)
        
        if len(post_desat_time_list) == 0:
            post_desat_SpO2 = average_SpO2_during_resp_event.loc[average_resp_event_low_peak_time:average_resp_event_low_peak_time + 50]
            max_post_desat_SpO2 = max(post_desat_SpO2.SpO2)
            search_window_end = min(post_desat_SpO2.loc[post_desat_SpO2.SpO2 == max_post_desat_SpO2].index)
        else:
            search_window_end = min(post_desat_time_list)

        self.search_window_resp_event_start = search_window_start
        self.search_window_resp_event_end = search_window_end

    def slice_average_SpO2_by_search_window(self): #slice average SpO2 by search window
        if len(self.average_SpO2_during_apnea) > 0:
            self.sliced_average_SpO2_during_apnea = self.average_SpO2_during_apnea.loc[self.search_window_apnea_start:self.search_window_apnea_end]
        else:
            self.sliced_average_SpO2_during_apnea = self.average_SpO2_during_apnea
        if len(self.average_SpO2_during_hypopnea) > 0:
            self.sliced_average_SpO2_during_hypopnea = self.average_SpO2_during_hypopnea.loc[self.search_window_hypopnea_start:self.search_window_hypopnea_end]
        else:
            self.sliced_average_SpO2_during_hypopnea = self.average_SpO2_during_hypopnea
        if len(self.average_SpO2_during_resp_event) > 0:
            self.sliced_average_SpO2_during_resp_event = self.average_SpO2_during_resp_event.loc[self.search_window_resp_event_start:self.search_window_resp_event_end]
        else:
            self.sliced_average_SpO2_during_resp_event = self.average_SpO2_during_resp_event

    def plot_average_SpO2_and_search_window(self): #plot average of SpO2 during apnea, hypopnea, and all respiratory events
        plt.figure(figsize=(8,5))
        plt.plot(self.average_SpO2_during_apnea.index, self.average_SpO2_during_apnea.SpO2, color = 'm', label = 'Apnea', alpha = 0.5)
        plt.plot(self.average_SpO2_during_hypopnea.index, self.average_SpO2_during_hypopnea.SpO2, color = 'y', label = 'Hypopnea', alpha = 0.5)
        plt.plot(self.average_SpO2_during_resp_event.index, self.average_SpO2_during_resp_event.SpO2, color = 'c', label = 'Apnea & Hypopnea')

        try:
            plt.plot([self.search_window_apnea_start, self.search_window_apnea_end], self.average_SpO2_during_apnea.loc[[self.search_window_apnea_start, \
                self.search_window_apnea_end]].SpO2, 'mv', markersize = 10, alpha = 0.5, label = 'Peak SpO2')
        except:
            pass
        plt.axvline(x = self.search_window_apnea_start, c = 'm', linestyle = '--', alpha = 0.5)
        plt.axvline(x = self.search_window_apnea_end, c = 'm', linestyle = '--', alpha = 0.5)

        try:
            plt.plot([self.search_window_hypopnea_start, self.search_window_hypopnea_end], self.average_SpO2_during_hypopnea.loc[[self.search_window_hypopnea_start, \
                self.search_window_hypopnea_end]].SpO2, 'yv', markersize = 10, alpha = 0.5, label = 'Peak SpO2')
        except:
            pass
        plt.axvline(x = self.search_window_hypopnea_start, c = 'y', linestyle = '--', alpha = 0.5)
        plt.axvline(x = self.search_window_hypopnea_end, c = 'y', linestyle = '--', alpha = 0.5)

        try:
            plt.plot([self.search_window_resp_event_start, self.search_window_resp_event_end], self.average_SpO2_during_resp_event.loc[[self.search_window_resp_event_start, \
                self.search_window_resp_event_end]].SpO2, 'cv', markersize = 10, alpha = 0.5, label = 'Peak SpO2')
        except:
            pass
        plt.axvline(x = self.search_window_resp_event_start, c = 'c', linestyle = '--', alpha = 0.5)
        plt.axvline(x = self.search_window_resp_event_end, c = 'c', linestyle = '--', alpha = 0.5)

        plt.legend(loc = 'lower left')
        plt.ylim(70,100)
        plt.title('Average SpO2 curve of respiratory events')
        plt.xlabel('Time (s)')
        plt.ylabel('SpO2 (%)')

        plt.show()

    def set_SpO2_by_search_window_apnea(self): #Set SpO2 by search window of apnea event
        for resp_event_index in self.apnea_dic:
            self.apnea_dic[resp_event_index].set_SpO2_by_search_window(self.search_window_apnea_start, self.search_window_apnea_end)

    def set_SpO2_by_search_window_hypopnea(self): #Set SpO2 by search window of hypopnea event
        for resp_event_index in self.hypopnea_dic:
            self.hypopnea_dic[resp_event_index].set_SpO2_by_search_window(self.search_window_hypopnea_start, self.search_window_hypopnea_end)

    def set_SpO2_by_search_window_resp_event(self): #Set SpO2 by search window of all respiratory event
        for resp_event_index in self.apnea_dic:
            self.apnea_dic[resp_event_index].set_SpO2_by_search_window(self.search_window_resp_event_start, self.search_window_resp_event_end)

        for resp_event_index in self.hypopnea_dic:
            self.hypopnea_dic[resp_event_index].set_SpO2_by_search_window(self.search_window_resp_event_start, self.search_window_resp_event_end)

    def calculate_hypoxic_burden(self, resp_event_dic): #hypoxic burden of respiratory event regardeless of desaturation
        hypoxic_burden_area = []
        if len(resp_event_dic) == 0:
            return 0
        for resp_event_index in resp_event_dic:
            resp_event = resp_event_dic[resp_event_index]
            SpO2_by_search_window = resp_event.SpO2_by_search_window.SpO2
            if len(SpO2_by_search_window) == 0:
                hypoxic_burden_area += [0]
                continue
            per = SpO2_by_search_window.index[1]-SpO2_by_search_window.index[0]
            hypoxic_burden_area += [(resp_event.baseline_SpO2 - SpO2)/(1/per) for SpO2 in SpO2_by_search_window if SpO2 < resp_event.baseline_SpO2]

        return sum(hypoxic_burden_area)/self.total_sleep_time/60 #unit: %min/hr

    def hypoxic_burden(self): #average: regardless, hypoxic burden: regardless
        self.get_Events()
        if len(self.Events) == 0:
            self.mean_apnea_dur = 0
            self.mean_hypopnea_dur = 0
            self.apnea_dic = {}
            self.hypopnea_dic = {}
            self.search_window_apnea_start = 0
            self.search_window_apnea_end = 0
            self.search_window_hypopnea_start = 0
            self.search_window_hypopnea_end = 0
            self.search_window_resp_event_start = 0
            self.search_window_resp_event_end = 0
            self.average_SpO2_during_apnea = pd.DataFrame(index = [i/2 for i in range(-100, 101)], columns = ['SpO2']).fillna(0)
            self.sliced_average_SpO2_during_apnea = pd.DataFrame(index = [], columns = ['SpO2'])
            self.average_SpO2_during_hypopnea = pd.DataFrame(index = [i/2 for i in range(-100, 101)], columns = ['SpO2']).fillna(0)
            self.sliced_average_SpO2_during_hypopnea = pd.DataFrame(index = [], columns = ['SpO2'])
            self.average_SpO2_during_resp_event = pd.DataFrame(index = [i/2 for i in range(-100, 101)], columns = ['SpO2']).fillna(0)
            self.sliced_average_SpO2_during_resp_event = pd.DataFrame(index = [], columns = ['SpO2'])
            return 0, 0, 0

        self.classify_Events()
        self.get_SpO2()
        self.generate_resp_event_dic()
        self.overlap_SpO2_of_resp_events()
        self.average_SpO2_of_resp_events()
        
        self.set_search_window_apnea()
        self.set_SpO2_by_search_window_apnea()
        hypoxic_burden_apnea = self.calculate_hypoxic_burden(self.apnea_dic)

        self.set_search_window_hypopnea()
        self.set_SpO2_by_search_window_hypopnea()
        hypoxic_burden_hypopnea = self.calculate_hypoxic_burden(self.hypopnea_dic)

        self.set_search_window_resp_event()
        self.set_SpO2_by_search_window_resp_event()
        hypoxic_burden_total = self.calculate_hypoxic_burden(self.apnea_dic) + self.calculate_hypoxic_burden(self.hypopnea_dic)

        self.slice_average_SpO2_by_search_window()
    
        return hypoxic_burden_apnea, hypoxic_burden_hypopnea, hypoxic_burden_total