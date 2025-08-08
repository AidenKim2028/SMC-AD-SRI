# This module has to run in Python 3.7 or above. (assuming dictionary to be ordered)

import csv
from datetime import datetime


class csv_read:

    def read_datanum(path):
        with open(path, newline="", encoding='utf-8') as input:

            # make a object and read datanum
            read_datanum = csv.reader(input, delimiter=",")
            for row in read_datanum:
                if len(row) == 0:
                    continue
                if row[0] != "Identity:":
                    continue
                if row[0] == "Identity:":
                    datanum = row[1]
                    break

        del read_datanum
        return datanum

    def read_age(path):
        with open(path, newline="", encoding='utf-8') as input:

            # make a object and read age
            read_age = csv.reader(input, delimiter=",")
            for row in read_age:
                if len(row) == 0:
                    continue
                if row[0] != "Age (at start of data collection):":
                    continue
                if row[0] == "Age (at start of data collection):":
                    age = row[1]
                    break

        del read_age
        return age

    def read_gender(path):
        with open(path, newline="", encoding='utf-8') as input:

            # make a object and read gender
            read_gender = csv.reader(input, delimiter=",")
            for row in read_gender:
                if len(row) == 0:
                    continue
                if row[0] != "Gender:":
                    continue
                if row[0] == "Gender:":
                    gender = row[1]
                    break

        del read_gender
        if gender == "Female":
            return "F"
        else:
            return "M"

    def read_name(path):
        with open(path, newline="", encoding='utf-8') as input:

            # make a object and read name
            read_name = csv.reader(input, delimiter=",")
            for row in read_name:
                if len(row) == 0:
                    continue
                if row[0] != "Full Name:":
                    continue
                if row[0] == "Full Name:":
                    name = row[1]
                    break

        del read_name
        return name

    def epoch_length(path):

        # initialize parameters
        epoch_length = 0

        with open(path, newline="", encoding='utf-8') as input:

            # make a object and read epoch length
            epoch_read = csv.reader(input, delimiter=",")
            for row in epoch_read:
                if len(row) == 0:
                    continue
                if row[0] != "Epoch Length:":
                    continue
                if row[0] == "Epoch Length:":
                    epoch_length = row[1]
                    break

        del epoch_read
        return epoch_length

    def epoch_dataread(path):

        # initialize parameters
        raw_data = {}

        with open(path, newline="", encoding='utf-8') as input:

            data_read = csv.reader(input, delimiter=",")
            flag1 = 0
            flag2 = 0
            flag3 = 0
            activerow = 0
            row_light = 0  # row num in light
            row_activity = 0  # row num in activity
            row_isawake = 0  # row num in awake

            for row in data_read:
                if flag2 == 1:
                    if len(row) == 0:
                        continue

                    datast = row[1]
                    timest = row[2]
                    combinest = datast + " " + timest
                    combine1 = datetime.strptime(combinest, "%Y-%m-%d %H:%M:%S")
                    isactive = row[row_isawake]
                    activity = row[row_activity]
                    light = row[row_light]
                    raw_data[combine1] = [isactive, activity, light]
                    continue

                if flag3 == 1:
                    if len(row) == 0:
                        continue

                    if row[0] != "1":
                        continue

                    if row[0] == "1":
                        datast = row[1]
                        timest = row[2]
                        combinest = datast + " " + timest
                        combine1 = datetime.strptime(combinest, "%Y-%m-%d %H:%M:%S")
                        isactive = row[row_isawake]
                        activity = row[row_activity]
                        light = row[row_light]
                        raw_data[combine1] = [isactive, activity, light]
                        flag2 = 1
                        continue

                if flag1 == 1:  # gather target inputs in legend
                    if row_light != 0 and row_activity != 0 and row_isawake != 0:
                        flag3 = 1  # trip flag3 to proceed data reading mode
                        continue

                    if len(row) == 0:
                        activerow = activerow + 1
                        continue

                    if row[0] == "Sleep/Wake:":
                        row_isawake = activerow - 4  # Sleep/Wake row
                        activerow = activerow + 1
                        continue
                    elif row[0] == "Activity:":
                        row_activity = activerow - 4  # Activity row
                        activerow = activerow + 1
                        continue
                    elif row[0] == "White Light:":
                        row_light = activerow - 4  # White Light row
                        activerow = activerow + 1
                        continue
                    else:
                        activerow = activerow + 1  # If otherwise not found, increment activerow
                        continue

                if len(row) == 0:  # skip blank line
                    continue

                if row[0] != "-------------------- Epoch-by-Epoch Data -------------------":
                    continue  # find index row

                if row[0] == "-------------------- Epoch-by-Epoch Data -------------------":
                    flag1 = 1  # trip the flag if the program finds epoch legend
                    activerow = activerow + 1
                    continue

        del data_read
        return raw_data

# read intervals
    def sleepinterval_read(path):
        interval_data = {}
        num = 1
        with open(path, newline="", encoding='utf-8') as input:
            data_read = csv.reader(input, delimiter=",")
            for row in data_read:
                if len(row) == 0:
                    continue
                elif row[0] != "SLEEP":
                    continue
                elif row[0] == "SLEEP":
                    if "NaN" in row[2:5]:
                        continue
                    datast1 = row[2]
                    timest1 = row[3]
                    combinest1 = datast1 + " " + timest1
                    combine1 = datetime.strptime(combinest1, "%Y-%m-%d %H:%M:%S")

                    datast2 = row[4]
                    timest2 = row[5]
                    combinest2 = datast2 + " " + timest2
                    combine2 = datetime.strptime(combinest2, "%Y-%m-%d %H:%M:%S")

                    length = row[6]
                    interval_data.update({num : [combine1, combine2, length]})
                    num = num + 1

        del data_read
        return interval_data

# read intervals
    def wakeinterval_read(path):
        interval_data = {}
        num = 1
        with open(path, newline="", encoding='utf-8') as input:
            data_read = csv.reader(input, delimiter=",")
            for row in data_read:
                if len(row) == 0:
                    continue
                elif row[0] != "ACTIVE":
                    continue
                elif row[0] == "ACTIVE":
                    if "NaN" in row[2:5]:
                        continue
                    datast1 = row[2]
                    timest1 = row[3]
                    combinest1 = datast1 + " " + timest1
                    combine1 = datetime.strptime(combinest1, "%Y-%m-%d %H:%M:%S")

                    datast2 = row[4]
                    timest2 = row[5]
                    combinest2 = datast2 + " " + timest2
                    combine2 = datetime.strptime(combinest2, "%Y-%m-%d %H:%M:%S")

                    length = row[6]
                    interval_data.update({num : [combine1, combine2, length]})
                    num = num + 1

        del data_read

        try:
            delkey = list(interval_data.keys())[0]
        except IndexError:
            return

        interval_data.pop(delkey)

        return interval_data
