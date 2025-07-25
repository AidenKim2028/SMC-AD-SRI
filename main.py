# Main.py - reads and adds Excel files input
import tkinter as tk
import csv
import os
from matlab_data import matlab_data
from patient_data import ptSRI_data
from tkinter import filedialog


def main():
    # drag file or prompt GUI or get an argument for the path of file
    # make a dict from the file, each entity corresponding for the data for each patient
    # one argument -> one file, one class, and one output

    # bring out the GUI! -> prompt user to input xls file or folder
    # make a new object one by one - loop
    # call patient_data class then make class churn out the parameters when initialized 
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilenames(defaultextension="csv", title="Select Philips Actiwatch csv file")
    file_path3 = filedialog.askopenfilename(defaultextension="csv", title="Select Diagnosis list csv file")
    file_path2 = filedialog.asksaveasfilename(defaultextension="csv", title="Specify csv file to store parameters")

    filelist = []
    pt_dxlist = {}

    # Reads patient's PSG diagnosis
    with open(file_path3, newline="", encoding='utf-8') as input:

        # read diagnoses
        read_dx = csv.reader(input, delimiter=",")
        for row in read_dx:
            if len(row) == 0:
                continue
            else:
                datanum, dx = row[0], row[1]
                pt_dxlist.update({datanum: dx})

    del read_dx

    print("datanum S/A patient's name and num       Dx      SRI        sleepmedian   TST TST_day TST_night")
    print("===============================================================================================")

    # specify parameters for epoch data
    epoch_length = 120  # epoch length in seconds

    # exportmode
    # 0 = dont export
    # 1 = csv, 2 = png
    # 3 = activity data (returns array)
    # 4 = period activity sum
    exportmode = 4

    # parameter for correction
    gamma = 0.1
    isresize = 0

    # export array pool
    exp_120_24 = []
    exp_120_6h = []
    exp_120_8h = []
    exp_120_10h = []
    exp_600_24 = []
    exp_600_6h = []
    exp_600_8h = []
    exp_600_10h = []
    exp_3600_24 = []
    exp_3600_6h = []
    exp_3600_8h = []
    exp_3600_10h = []
    actexp = []

    # for every xls file in file_path received, make out an object from this
    # matlab_data(ptSRI_data, is_24hour, epoch_length, interval, fliepath, exportmode, list, isexportdone)
    for files in file_path:
        a = ptSRI_data(files, pt_dxlist)
        print(a.datanum, a.gender + "/" + a.age, a.name, a.diagnosis, a.SRI, a.sleepmedian, a.tst, a.tstday, a.tstnight)
        filelist.append(a)

        if exportmode == 1 or exportmode == 2 or exportmode == 3:
            matlab_data.proc_data(a, 1, 120, 0, files, exportmode, gamma, isresize, exp_120_24, 0)
            matlab_data.proc_data(a, 0, 120, 360, files, exportmode, gamma, isresize, exp_120_6h, 1)
            matlab_data.proc_data(a, 0, 120, 480, files, exportmode, gamma, isresize, exp_120_8h, 2)
            matlab_data.proc_data(a, 0, 120, 600, files, exportmode, gamma, isresize, exp_120_10h, 3)

            matlab_data.proc_data(a, 1, 600, 0, files, exportmode, gamma, isresize, exp_600_24, 4)
            matlab_data.proc_data(a, 0, 600, 360, files, exportmode, gamma, isresize, exp_600_6h, 5)
            matlab_data.proc_data(a, 0, 600, 480, files, exportmode, gamma, isresize, exp_600_8h, 6)
            matlab_data.proc_data(a, 0, 600, 600, files, exportmode, gamma, isresize, exp_600_10h, 7)

            matlab_data.proc_data(a, 1, 3600, 0, files, exportmode, gamma, isresize, exp_3600_24, 8)
            matlab_data.proc_data(a, 0, 3600, 360, files, exportmode, gamma, isresize, exp_3600_6h, 9)
            matlab_data.proc_data(a, 0, 3600, 480, files, exportmode, gamma, isresize, exp_3600_8h, 10)
            matlab_data.proc_data(a, 0, 3600, 600, files, exportmode, gamma, isresize, exp_3600_10h, 11)

        elif exportmode == 4:
            matlab_data.interval_sum(a, actexp)

    with open(file_path2, "w", newline="", encoding='utf-8') as input:
        csvwriter = csv.writer(input)
        headerdata = ["datanum", "gender", "age", "name", "Dx", "SRI", "SleepMedian", "TST", "TST_day", "TST_night",
                      "avgActivity", "Totallight"]
        for i in range(0, 12):
            headerdata.append("isexportdone" + str(i+1))
        for i in range(0, 24):
            headerdata.append("TST" + str(i))
        for i in range(0, 24):
            headerdata.append("Light" + str(i))
        csvwriter.writerow(headerdata)

        for patient in filelist:
            row = [patient.datanum, patient.gender, patient.age, patient.name, patient.diagnosis, patient.SRI, patient.sleepmedian,
                   patient.tst, patient.tstday, patient.tstnight, patient.avgactivity, patient.totallightexp]
            for i in range(0, 12):
                row.append(patient.isexport[i])
            for i in range(0, 24):
                row.append(patient.tstarray[i])
            for i in range(0, 24):
                row.append(patient.lightexparray[i])
            csvwriter.writerow(row)

        input.close()

    (head, tail) = os.path.split(file_path2)

    head = head + "/matlab/"
    if os.path.exists(head) == 0:
        os.makedirs(head)

    if exportmode == 3:
        writecsv_fromarray(head, "24h_120s", exp_120_24)
        writecsv_fromarray(head, "sleep6h_120s", exp_120_6h)
        writecsv_fromarray(head, "sleep8h_120s", exp_120_8h)
        writecsv_fromarray(head, "sleep10h_120s", exp_120_10h)
        writecsv_fromarray(head, "24h_600s", exp_600_24)
        writecsv_fromarray(head, "sleep6h_600s", exp_600_6h)
        writecsv_fromarray(head, "sleep8h_600s", exp_600_8h)
        writecsv_fromarray(head, "sleep10h_600s", exp_600_10h)
        writecsv_fromarray(head, "24h_3600s", exp_3600_24)
        writecsv_fromarray(head, "sleep6h_3600s", exp_3600_6h)
        writecsv_fromarray(head, "sleep8h_3600s", exp_3600_8h)
        writecsv_fromarray(head, "sleep10h_3600s", exp_3600_10h)

    if exportmode == 4:
        writecsv_fromarray(head, "activitysum", actexp)

    # receive the parameters then make database out from it
    # make a dict - xls_file, pt's name, hash. this acts as an indices for the classes

    # then you store the database for further analyses
    # export xls file for statistical analysis
    # diff data then add new data then save the file.


def writecsv_fromarray(path, tail, array):
    path1 = path + tail + ".csv"
    with open(path1, "w", newline="", encoding='utf-8') as input:
        csvwriter = csv.writer(input)
        for i in array:
            newrow = i[4:]
            csvwriter.writerow(newrow)
        input.close()

    path2 = path + tail + "dx" + ".csv"
    with open(path2, "w", newline="", encoding='utf-8') as input2:
        csvwriter = csv.writer(input2)
        for i in array:
            newrow1 = i[0:4]
            csvwriter.writerow(newrow1)
        input2.close()


if __name__ == "__main__":
    main()
