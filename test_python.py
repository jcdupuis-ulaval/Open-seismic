import serial
import fnmatch
import os
import re



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

        output_file = open('{}{}.txt'.format(name, num), 'w')


        ser.write("{} 1".format(command).encode())
        line = ser.read_until('packets : '.encode())
        numberOfSample = int(ser.read_until().decode("utf-8"))
        for i in range(numberOfSample-3):
            line = ser.readline()
            line = line.decode("utf-8")
            if line.count(',') == 1:
                output_file.write(line)
        ser.write("{} 2".format(command).encode())
        line = ser.read_until('packets : '.encode())
        numberOfSample = int(ser.read_until().decode("utf-8"))
        for i in range(numberOfSample - 3):
            line = ser.readline()
            line = line.decode("utf-8")
            if line.count(',') == 1:
                output_file.write(line)

        output_file.close()
        print('file close')

    # print(command)

    # rep = ser.read()
    # print(rep)
