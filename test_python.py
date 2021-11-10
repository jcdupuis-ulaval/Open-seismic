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



        ser.write("{} 1".format(command).encode())
        line = ser.read_until('packets : '.encode())
        numberOfSample = int(ser.read_until().decode("utf-8"))
        temps1 = np.zeros((numberOfSample-5))
        seis1 = np.zeros((numberOfSample-5))
        for i in range(numberOfSample-5):
            line = ser.readline()
            line = line.decode("utf-8")
            if line.count(',') == 1:
                # output_file.write(line)
                temp = line.split(',')
                temps1[i] = int(temp[0])
                seis1[i] = int(temp[1])



        ser.write("{} 2".format(command).encode())
        line = ser.read_until('packets : '.encode())
        numberOfSample = int(ser.read_until().decode("utf-8"))
        temps2 = np.zeros((numberOfSample - 5))
        seis2 = np.zeros((numberOfSample - 5))
        for i in range(numberOfSample - 5):
            line = ser.readline()
            line = line.decode("utf-8")
            if line.count(',') == 1:
                # output_file.write(line)
                temp = line.split(',')
                temps2[i] = int(temp[0])
                seis2[i] = int(temp[1])


        plt.plot(temps1, seis1, label="ADC 1")
        plt.plot(temps2, seis2, label="ADC 2")
        plt.show()

    elif command == 'save':
        output_file = open('{}{}.txt'.format(name, num), 'w')
        for i, sample in enumerate(temps1):
            output_file.write("{},{},{},{} \n".format(sample, seis1[i],temps2[i],seis2[i]))

        output_file.close()
        print('file close')

    # print(command)

    # rep = ser.read()
    # print(rep)
