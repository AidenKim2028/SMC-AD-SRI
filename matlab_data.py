import os
import datetime
import csv
import numpy as np
from patient_data import ptSRI_data
from PIL import Image


# This class concatenates 5-day data into a single parallel table
# Merges epoch if needed (since epoch length of actiwatch varies over patient data)

"""

# ver1 : sleep_bool + activity + light data
         yielded no meaningful data.
         tried output for 5-convoluted layers - fits well but no meaningful result
         maybe try more on raw number data? or try gamma correction?
# ver2 : export just activity data and try it again? -> does not work

"""

class matlab_data:
    def proc_data(pt: ptSRI_data, is_24hour: bool, epoch_matlab: int, interval: int, files, exportmode, gamma, isresize, exp_list, isexportdone):
        if pt.SRI == 999:
            return

        export = []
        pad_data = {}
        merge_data = {}

        number_avg = 1

        # see if epoch is shorter than input
        if epoch_matlab > pt.epoch_length:
            number_avg = int(epoch_matlab / pt.epoch_length)

        # I need more than 5 sleep intervals!
        if len(pt.interval.items()) < 5:
            return

        """
        # 24hour or 6h/8h/10h -> pad
        # 6h/8h/10h - read the interval, validate the interval (by looking at LUT) 
                      exception when valid data is not found
        """

        if is_24hour:
            # pad the data if invalid - zero padding
            for (key, value) in pt.trim_data.items():
                pad_data.update({key: [0 if i == 'NaN' else i for i in value]})
            epoch_inaday = int(86400 / epoch_matlab)

        else:
            epoch_inaday = int(interval * 60 / epoch_matlab)
            epoch_inaday2 = int(interval * 60 / pt.epoch_length)

            # get the sleep interval data
            for (key, i) in pt.interval.items():
                lookup_starttime = i[0]
                lookup_endtime = i[0] + datetime.timedelta(minutes=interval)
                lookup_startdate = lookup_starttime.date()
                lookup_enddate = lookup_endtime.date()
                try:
                    pt.isvalidLUT[lookup_enddate]
                except KeyError:
                    continue

                if pt.isvalidLUT[lookup_startdate] == 0 or pt.isvalidLUT[lookup_enddate] == 0:
                    continue
                else:
                    k = lookup_starttime
                    for it in range(epoch_inaday2):
                        try:
                            pad_before = pt.raw_data[k]
                        except KeyError:
                            continue
                        pad_after = [0 if i == 'NaN' else i for i in pad_before]
                        pad_data.update({k: pad_after})
                        k = k + datetime.timedelta(seconds=pt.epoch_length)

        pad_key_arr = list(pad_data.keys())

        i = 0

        while 1:
            issleepsum = 0
            activitysum = 0
            lightsum = 0

            for a1 in range(number_avg):
                j = i + a1
                try:
                    pad_key = pad_key_arr[j]
                    issleepsum = issleepsum + int(pad_data[pad_key][0])
                    activitysum = activitysum + int(pad_data[pad_key][1])
                    lightsum = lightsum + float(pad_data[pad_key][2])
                except IndexError:
                    break

            issleep = issleepsum / number_avg
            activity = activitysum
            light = lightsum / number_avg

            key = pad_key_arr[i]
            merge_data.update({key: activity})

            try:
                i = i + number_avg
                pad_key_arr[i]
            except IndexError:
                break

        merge_key_arr = list(merge_data.keys())

        if len(merge_key_arr) < epoch_inaday * 5:
            return

        for i in range(epoch_inaday):
            i2 = i + epoch_inaday
            i3 = i + epoch_inaday * 2
            i4 = i + epoch_inaday * 3
            i5 = i + epoch_inaday * 4

            k1 = merge_key_arr[i]
            k2 = merge_key_arr[i2]
            k3 = merge_key_arr[i3]
            k4 = merge_key_arr[i4]
            k5 = merge_key_arr[i5]

            export_arr = [merge_data[k1], merge_data[k2], merge_data[k3], merge_data[k4], merge_data[k5]]
            export.append(export_arr)

        if is_24hour == 0:
            str_is24hour = "sleep" + str(interval) + "m"
        else:
            str_is24hour = "24h"

        (head, tail) = os.path.split(files)

        head = head + "/matlab" + "/" + "epoch" + str(epoch_matlab) + "s/" + str_is24hour + "/" + pt.diagnosis
        if os.path.exists(head) == 0:
            os.makedirs(head)

        file_path3 = head + "/" + tail[0:7]

        pt.isexport[isexportdone] = 1

        if exportmode == 1:
            exportcsv(file_path3, export)

        if exportmode == 2:
            exportpng(file_path3, export, gamma, isresize)

        if exportmode == 3:
            exportrow = []
            if pt.diagnosis == "Normal":
                exportrow = exportrow + [1,0,0,0]
            elif pt.diagnosis == "Insomnia":
                exportrow = exportrow + [0,1,0,0]
            elif pt.diagnosis == "OSA":
                exportrow = exportrow + [0,0,1,0]
            elif pt.diagnosis == "COMISA":
                exportrow = exportrow + [0,0,0,1]
            elif pt.diagnosis == "none":
                return

            for i in range(epoch_inaday * 5):
                key = merge_key_arr[i]
                exportrow.append(merge_data[key])

            exp_list.append(exportrow)


    def interval_sum(pt: ptSRI_data, exp_list):
        if pt.SRI == 999:
            return

        sleep_act_array = []
        wake_act_array = []

        # I need more than 5 intervals!
        if len(pt.interval.items()) < 5 or len(pt.interval_wake.items()) < 5:
            return

        """
        # count each day's activity, average it and make an array out of this
        # count every interval, regardless of the day, average each period
    
        """

        # get the interval data
        # first, sleep one

        for (key, i) in pt.interval.items():
            lookup_starttime = i[0]
            lookup_endtime = i[1]
            lookup_startdate = lookup_starttime.date()
            lookup_enddate = lookup_endtime.date()
            length = lookup_endtime - lookup_starttime
            epoch_ina_period = int(length.total_seconds() / pt.epoch_length)
            sum_activity = 0

            try:
                pt.isvalidLUT[lookup_enddate]
            except KeyError:
                continue

            if pt.isvalidLUT[lookup_startdate] == 0 or pt.isvalidLUT[lookup_enddate] == 0:
                continue

            else:
                k = lookup_starttime
                for it in range(epoch_ina_period):
                    try:
                        list_fromraw = pt.raw_data[k]
                        if list_fromraw[1] == "NaN":
                            pad = 0
                        else:
                            pad = float(list_fromraw[1])
                        sum_activity = sum_activity + pad
                    except KeyError:
                        continue
                    k = k + datetime.timedelta(seconds=pt.epoch_length)

                avg_activity = sum_activity / epoch_ina_period
                sleep_act_array.append(avg_activity)

        for (key, i) in pt.interval_wake.items():
            lookup_starttime = i[0]
            lookup_endtime = i[1]
            lookup_startdate = lookup_starttime.date()
            lookup_enddate = lookup_endtime.date()
            length = lookup_endtime - lookup_starttime
            epoch_ina_period = int(length.total_seconds() / pt.epoch_length)
            sum_activity = 0

            try:
                pt.isvalidLUT[lookup_enddate]
            except KeyError:
                continue

            if pt.isvalidLUT[lookup_startdate] == 0 or pt.isvalidLUT[lookup_enddate] == 0:
                continue

            else:
                k = lookup_starttime
                for it in range(epoch_ina_period):
                    try:
                        list_fromraw = pt.raw_data[k]
                        if list_fromraw[1] == "NaN":
                            pad = 0
                        else:
                            pad = float(list_fromraw[1])
                        sum_activity = sum_activity + pad
                    except KeyError:
                        continue
                    k = k + datetime.timedelta(seconds=pt.epoch_length)

                avg_activity = sum_activity / epoch_ina_period
                wake_act_array.append(avg_activity)

        if len(sleep_act_array) < 5 or len(wake_act_array) < 5:
            return

        exportrow = []
        """
        # Script to export diagnoses in CSV

        if pt.diagnosis == "Normal":
            exportrow = exportrow + [1, 0, 0, 0]
        elif pt.diagnosis == "Insomnia":
            exportrow = exportrow + [0, 1, 0, 0]
        elif pt.diagnosis == "OSA":
            exportrow = exportrow + [0, 0, 1, 0]
        elif pt.diagnosis == "COMISA":
            exportrow = exportrow + [0, 0, 0, 1]
        elif pt.diagnosis == "none":
            return
        """

        """
        # Only see difference btw Normal and OSA
        if pt.diagnosis == "Normal":
            exportrow = exportrow + [pt.diagnosis, 0, 0, 0]
        elif pt.diagnosis == "Insomnia":
            return
        elif pt.diagnosis == "OSA":
            exportrow = exportrow + [pt.diagnosis, 0, 0, 0]
        elif pt.diagnosis == "COMISA":
            return
        elif pt.diagnosis == "none":
            return
"""

        # Diagnosis and name
        if pt.diagnosis == "Normal":
            exportrow = [pt.datanum] + exportrow + [pt.diagnosis]
        elif pt.diagnosis == "Insomnia":
            exportrow = [pt.datanum] + exportrow + [pt.diagnosis]
        elif pt.diagnosis == "OSA":
            exportrow = [pt.datanum] + exportrow + [pt.diagnosis]
        elif pt.diagnosis == "COMISA":
            exportrow = [pt.datanum] + exportrow + [pt.diagnosis]
        elif pt.diagnosis == "none":
            return

        for i in range(5):
            exportrow.append(sleep_act_array[i])
            exportrow.append(wake_act_array[i])

        exp_list.append(exportrow)


def exportcsv(file_path3, export):
    file_path3 = file_path3 + ".csv"
    with open(file_path3, "w", newline="", encoding='utf-8') as input:
        csvwriter = csv.writer(input)
        for i in export:
            csvwriter.writerow(i)
        input.close()

def exportpng(file_path3, export, gamma, isresize):
    if gamma != 1:
        file_path3 = file_path3 + "_gamma" + str(gamma)
    file_path3 = file_path3 + ".png"
    numpy_array = np.array(export)

    if isresize:
        export_array = np.zeros((1,50))
    else:
        export_array = np.zeros((1,5))

    max_activity = np.amax(numpy_array)
    column_max_array = np.tile(np.array([max_activity]), 5)

    for i in numpy_array:
        # normalize
        row1 = np.divide(i, column_max_array)
        row2 = np.power(np.subtract(np.ones((1,5)), row1), 1/gamma)
        row3 = np.rint(row2 * 255)

        if isresize:
            # resize
            row4 = np.kron(row3, np.ones((5, 10)))
            export_array = np.vstack((export_array, row4))

        else:
            export_array = np.vstack((export_array, row3))

    export_array = np.delete(export_array, 0, 0)
    export_array = np.transpose(export_array)
    img = Image.fromarray(export_array.astype(np.uint8), mode="L")
    img.save(file_path3)
