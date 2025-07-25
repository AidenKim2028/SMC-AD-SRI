from csv_read import csv_read
from datetime import time, timedelta
import math


class ptSRI_data:

    def __init__(self, path, pt_dxlist):
        # for each argument does not exist, make a new object from the index
        # object contains var 'name, data, hash, SRI, median sleep time'
        # get name (anthropoaedic data) and sleep data -> calc hash, SRI, median sleep time, then boom
        # add each entity from calculated data into the database
        self.path = path
        self.isvalidLUT = {}

        self.datanum = csv_read.read_datanum(self.path)
        self.name = csv_read.read_name(self.path)
        self.gender = csv_read.read_gender(self.path)
        self.age = csv_read.read_age(self.path)

        self.epoch_length = int(csv_read.epoch_length(self.path))  # in seconds
        self.raw_data = csv_read.epoch_dataread(self.path)  # isoTimestamp, issleeping
        self.trim_data = self.trimdata(self.raw_data, self.epoch_length)

        self.interval = csv_read.sleepinterval_read(self.path)
        self.interval_wake = csv_read.wakeinterval_read(self.path)
        self.isexport = [0,0,0,0,0,0,0,0,0,0,0,0]

        try:
            self.diagnosis = pt_dxlist[self.datanum]
        except KeyError:
            self.diagnosis = "none"


        number_days = math.ceil(len(self.trim_data) / (86400 / self.epoch_length))
        if number_days < 5:
            self.SRI = 999
            self.sleepmedian = -1
            self.tstarray = ["invalid", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            self.tst = -1
            self.tstday = -1
            self.tstnight = -1
            self.avgactivity = -1
            self.lightexparray = ["invalid", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            self.totallightexp = -1
            return

        self.SRI = self.calc_SRI(self.trim_data, self.epoch_length)  # calculate out from dict
        self.sleepmedian = self.calc_sleepmedian(self.trim_data, self.epoch_length)  # in seconds
        self.tstarray = self.calc_totalsleeptime(self.trim_data, self.epoch_length)
        tstparamarray = self.calc_totalsleepparam(self.tstarray)
        self.tst = tstparamarray[0]
        self.tstday = tstparamarray[1]
        self.tstnight = tstparamarray[2]

        # self.totalsleeptime = self.calc_totalsleeptime(self.raw_data, self.epoch_length, self.sleepmedian) # in sec
        # self.daily_SRI = calc_dailySRI(self.rawdata, self.epoch_length)          
        # self.calc_hash = calc_hash(self.raw_data)

        self.avgactivity = self.calc_avgactivity(self.trim_data, self.epoch_length)

        self.lightexparray = self.calc_dailylightexpo(self.trim_data, self.epoch_length)
        self.totallightexp = self.calc_totallightexpparam(self.lightexparray)


    # raw_data from csv returns a dict - {timestamp(datetime object), [isactive, activity, light]}

    def trimdata(self, raw_data, epoch_length):
        # trim the data and serialize the day, make new dict out from raw data dict
        # input - {timestamp(datetime object), [isactive, activity, light]}
        # output - {(serialized_day, timestamp), [isactive, activity, light]}
        # this also output LUT value for validity

        epoch_inaday = int(86400 / epoch_length)
        valid_date = []
        valid_epochs = 0
        trim_data = {}

        datelist = raw_data.keys()
        startdate = list(datelist)[0]

        daycount = 0
        datecount = startdate

        self.isvalidLUT.update({datecount.date(): 0})

        for i in raw_data:  # scan for valid date!
            if i.date() == datecount.date():
                if raw_data[i][0] == "0" or raw_data[i][0] == "1":
                    valid_epochs = valid_epochs + 1

            if i.date() != datecount.date():
                if valid_epochs >= (epoch_inaday * 22 / 24):
                    valid_date.append(datecount.date())  # this makes out dict consisted of valid dates
                    self.isvalidLUT[datecount.date()] = 1

                datecount = datecount + timedelta(days=1)
                valid_epochs = 0
                self.isvalidLUT[datecount.date()] = 0

                if raw_data[i][0] == "0" or raw_data[i][0] == "1":
                    valid_epochs = valid_epochs + 1

        a = list(self.isvalidLUT.keys())
        self.isvalidLUT[a[0]] = 1
        self.isvalidLUT[a[-1]] = 1

        datecount = startdate  # reinitialize daycount

        for i in raw_data:  # make a serialized list for days
            if i.date() == datecount.date():
                if i.date() in valid_date:
                    a = i.time()
                    trim_data.update({(daycount, a.isoformat()): raw_data[i]})

            if i.date() != datecount.date():
                datecount = datecount + timedelta(days=1)
                if i.date() in valid_date:
                    daycount = daycount + 1
                    a = i.time()
                    trim_data.update({(daycount, a.isoformat()): raw_data[i]})

        return trim_data

    def calc_SRI(self, trim_data, epoch_length):
        # get input from the file passed on - this should accept new object for the argument
        # read name, the whole epoch files
        # compare each epoch day, compute out SRI every day.
        # or compare all epochs recorded then compute whole SRI for the whole set
        # return the value, retaining the variable calculated inside
        # epoch - 0 is sleeping, 1 is awake

        # initialize the variable
        issame_epoch = 0
        total_epoch = 0
        epoch_inaday = int(86400 / epoch_length)

        # compare rows from array
        for i in trim_data:
            countday = i[0]
            counttime = i[1]
            k = countday + 1

            try:
                trim_data[(k, counttime)]
            except KeyError:
                continue

            total_epoch = total_epoch + 1
            if trim_data[(countday, counttime)][0] == trim_data[(k, counttime)][0]:
                issame_epoch = issame_epoch + 1

        SRI = -100 + 200 * issame_epoch / total_epoch
        return SRI

    def calc_sleepmedian(self, trim_data, epoch_length):
        # get input from the file passed on - this should accept new object for the argument
        # calculate sleep median day - returns value in seconds

        sinsum = float(0)
        cossum = float(0)
        pi = math.pi

        for timest in trim_data.keys():
            timeiso = time.fromisoformat(timest[1])
            timeinsec = timeiso.hour * 3600 + timeiso.minute * 60 + timeiso.second
            if trim_data[timest][0] == "0" or trim_data[timest][0] == "1":
                sinsum = sinsum + math.sin(2 * pi * timeinsec / 86400) * (float(trim_data[timest][0]) - 1) * -1
                cossum = cossum + math.cos(2 * pi * timeinsec / 86400) * (float(trim_data[timest][0]) - 1) * -1
            else:
                continue

        sleepmedian_insec = 86400 / (2 * pi) * math.atan2(sinsum, cossum)
        return sleepmedian_insec

    def calc_totalsleeptime(self, trim_data, epoch_length):
        # calculates hourly total sleep time averaged by daily basis

        total_days = math.ceil(len(trim_data) / (86400 / epoch_length))

        epoch_issleeping = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        time_issleeping = []

        for timest in trim_data.keys():
            timeiso = time.fromisoformat(timest[1])
            if trim_data[timest][0] == "0":
                epoch_issleeping[timeiso.hour] = epoch_issleeping[timeiso.hour] + 1

        for i in range(len(epoch_issleeping)):
            time_issleeping.append(epoch_issleeping[i] * epoch_length / total_days)

        return time_issleeping

    def calc_totalsleepparam(self, tstarray):
        # calculates TSTparams out from tstarray
        tst = 0
        tst_day = 0
        tst_night = 0

        for i in range(len(tstarray)):
            tst = tst + tstarray[i]
            if 10 <= i < 22:
                tst_day = tst_day + tstarray[i]
            else:
                tst_night = tst_night + tstarray[i]

        return [tst, tst_day, tst_night]

    def calc_avgactivity(self, trim_data, epoch_length):
        # calculates average activity - per all epoch. Bascially (sum of activity)/(all epoch)

        sum_activity = 0

        for i in trim_data:

            if trim_data[i][1] == "NaN":
                activity = 0
            else:
                activity = float(trim_data[i][1])
            sum_activity = sum_activity + activity

        avg_activity = sum_activity / len(trim_data)
        return avg_activity

    def calc_dailylightexpo(self, trim_data, epoch_length):
        # calculates minutes > 250lux by hourly basis

        total_days = math.ceil(len(trim_data) / (86400 / epoch_length))

        epoch_islightexp = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        time_islightexp = []

        for timest in trim_data.keys():
            timeiso = time.fromisoformat(timest[1])
            light = float(trim_data[timest][2])
            if light >= 250:
                epoch_islightexp[timeiso.hour] = epoch_islightexp[timeiso.hour] + 1

        for i in range(len(epoch_islightexp)):
            time_islightexp.append(epoch_islightexp[i] * epoch_length / total_days)

        return time_islightexp

    def calc_totallightexpparam(self, lightexparray):
        # calculates light exposure min param from lightexparray
        total_activity = sum(lightexparray)

        return total_activity

    # def daily_SRI():
    # based on sleep median time calculated, daily SRI is based on epochs cut on arbitrary cut time
    # unless otherwise specified, this function cuts day on the time right opposite of the calculated sleep median

    # def calc_hash():
    # calculate out the hash out from epochs recorded.
    # this makes sure the patient's epochs are not interchanged
