import serial, time

ser = serial.Serial("/dev/ttyUSB0", 115200)

class RangeRead:
    def __init__(self):
        self.init()
    # set to mm for measure unit
    # command 5A 05 05 06 6A - set to mm
    #  command 5A 05 05 01 65 - set to cm
    # cpmmand 5A 04 11 6F - save settings
    def init(self):
        # ser.write('5A 05 05 01 65')
        ser.write('5A 05 05 06 6A')
        ser.write('5A 04 11 6F')
        ser.reset_input_buffer()

    def getTFminiData(self):
        while True:
            count = ser.in_waiting
            if count > 8:
                recv = ser.read(9)
                ser.reset_input_buffer()
                if recv[0] == 'Y' and recv[1] == 'Y':  # 0x59 is 'Y'
                    low = int(recv[2].encode('hex'), 16)
                    high = int(recv[3].encode('hex'), 16)
                    distance = low + (high << 8)
                    print(distance, ' mm')
                    time.sleep(0.1)


if __name__ == '__main__':
    try:
        if ser.is_open == False:
            ser.open()
        reader = RangeRead()
        reader.getTFminiData()
    except KeyboardInterrupt:  # Ctrl+C
        if ser != None:
            ser.close()