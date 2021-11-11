import matplotlib.pyplot as plt
import numpy as np
import serial
import fnmatch
import os
import re
import matplotlib.pyplot as pl



serial_port = 'COM9'
baud_rate = 115200  # In arduino, Serial.begin(baud_rate)

ser = serial.Serial(serial_port, baud_rate)

ON = True

while ON:
    command = input()
    if command == 'exit':
        ON = False
        break
    elif command == 'arm':
        ser.write("{}".format(command).encode())
        line = ser.readline()
        line = line.decode("utf-8")
        print(line)
        line = ser.read_until()
        print(line.decode("utf-8"))
    elif command == 'harvest':

        ser.write("{} 1".format(command).encode())
        line = ser.read_until('packets : '.encode())
        numberOfSample = int(ser.read_until().decode("utf-8"))
        temps1 = np.zeros((numberOfSample-5))
        seis1 = np.zeros((numberOfSample-5))
        for i in range(numberOfSample-5):
            line = ser.readline()
            line = line.decode("utf-8")
            temp = line.split(',')
            if line.count(',') == 1:
                temps1[i] = int(temp[0])
                seis1[i] = int(temp[1])
        temps1 = (temps1 - temps1[0]) / 1E6
        range_accel = (4.1 - 0.0021) * 2
        seis1 = (seis1 * range_accel) / (2 ** 24)
        seis1_mod = np.zeros((len(seis1)))
        for i, val in enumerate(seis1):
            if val > 4.096:
                seis1_mod[i] = val - range_accel
            else:
                seis1_mod[i] = val





        ser.write("{} 2".format(command).encode())
        line = ser.read_until('packets : '.encode())
        numberOfSample = int(ser.read_until().decode("utf-8"))
        temps2 = np.zeros((numberOfSample - 5))
        seis2 = np.zeros((numberOfSample - 5))
        for i in range(numberOfSample-5):
            line = ser.readline()
            line = line.decode("utf-8")
            temp = line.split(',')
            if line.count(',') == 1:
                temps2[i] = int(temp[0])
                seis2[i] = int(temp[1])
        temps2 = (temps2 - temps2[0]) / 1E6
        range_accel = (4.1 - 0.0021) * 2
        seis2 = (seis2 * range_accel) / (2 ** 24)
        seis2_mod = np.zeros((len(seis2)))
        for i, val in enumerate(seis2):
            if val > 4.096:
                seis2_mod[i] = val - range_accel
            else:
                seis2_mod[i] = val




        plt.plot(temps1, seis1_mod, label="ADC 1")
        plt.plot(temps2, seis2_mod, label="ADC 2")
        plt.show()

    elif command == 'save':
        name = 'hop'
        ROOT = './'

        # I'm supposing that each item in ROOT folder that matches
        # 'somefile*.txt' is a file which we are looking for
        files = fnmatch.filter((f for f in os.listdir(ROOT)), '{}*.txt'.format(name))

        if not files:  # is empty
            num = ''
        elif len(files) == 1:
            num = '(1)'
        else:
            # files is supposed to contain 'somefile.txt'
            files.remove('{}.txt'.format(name))
            num = '(%i)' % (int(re.search(r'\(([0-9]+)\)', max(files)).group(1)) + 1)
        output_file = open('{}{}.txt'.format(name, num), 'w')
        for i, sample in enumerate(temps1):
            output_file.write("{},{},{},{} \n".format(sample, seis1_mod[i],temps2[i],seis2_mod[i]))

        output_file.close()
        print('file close')

    # print(command)

    # rep = ser.read()
    # print(rep)
