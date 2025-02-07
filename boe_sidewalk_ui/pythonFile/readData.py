#!/usr/bin/env python

import rospy
# from sidewalkbot_ws.src.sidewalkbot.msg import SlopeData
# from sidewalkbot.msg import SlopeData
from std_msgs.msg import Float32MultiArray
from std_msgs.msg import String
from std_msgs.msg import Float32
from std_msgs.msg import Time
import serial
import datetime as time
import csv

# port
portGPS = "/dev/ttyACM0"
portDigitalLevel = "/dev/ttyUSB0"

class ReadData:
    def __init__(self):
        self.serialGPS = serial.Serial(portGPS, baudrate=9600, timeout=0.5)
        self.serialDig = serial.Serial(portDigitalLevel, baudrate=9600, timeout=1)
        self.lat = 0.0
        self.lon = 0.0
        self.x_slope = 0.0
        self.y_slope = 0.0
        self.x_level_temp = 0.0
        self.y_level_temp = 0.0
        self.gpsDT = ""
        self.gpsData = ""
        self.time_pub = rospy.Publisher('current_time', String, queue_size=1)
        self.pub = rospy.Publisher('rover_data', String, queue_size=1)
        self.rate = rospy.Rate(1)
        self.raw_data = " "

    def __del__(self):
        self.serialGPS.close()
        self.serialDig.close()

    def getDigitalLevel(self):
        data = (str(self.serialDig.read(9600).decode('ascii', 'ignore'))).split("DEF")
        # print(data)
        # print (data)
        sdata = data[0].split("ABC")
        ddata = sdata[-1].split(" ")
        if len(ddata) >= 9:
            self.x_level_temp = ddata[1]
            self.y_level_temp = ddata[4]
            self.x_slope = ddata[3]
            self.y_slope = ddata[6]
            # print(self.x_level_temp, self.x_slope, self.y_level_temp, self.y_slope)

    def get_GPS(self):
        data = (str(self.serialGPS.readline().decode())).split(",")
        if data[0] == "$GPRMC":
            self.get_time(data)
            self.updateGPS(data)


    def updateGPS(self, data):
        self.lat = self.decode(data[3], self.lat)
        self.lon = self.decode(data[5], self.lon)
        self.gpsData = ', '.join(data)
        # if (data[2] == 'A'):
        #     s = data[9][0:-2] + '20' + data[9][-2:]+ ' ' + data[1]
        #     self.gpsDT = time.datetime.strptime(s, '%d%m%y %H%M%S.00') - time.timedelta(hours=7)

    def decode(self, coord, old_value):
        try:
            x = coord.split(",")
            head = x[0]
            tail = x[1]
            deg = float(head[0:-2])
            min = float(head[-2:] + "." + tail) *(1/ 60)
            return deg + min
        except:
            return old_value

    def get_time(self, data):
        if(data[2] == 'A'):
            cd = time.datetime.strptime(str(data[9]), '%d%m%y')
            ct = time.datetime.strptime(str(data[1]), '%H%M%S.%f')
            curr = time.datetime.strptime(str(cd.strftime('%y%m%d'))+' ' + str(ct.strftime('%H:%M:%S')), '%y%m%d %H:%M:%S') - time.timedelta(hours=7)
            self.gpsDT = '20' + curr.strftime('%y_%m_%d_') + curr.strftime('%H_%M_%S')
        else:
            self.gpsDT = (time.datetime.today()).strftime("%Y_%m_%d_%H_%M_%S")

    def send_data(self):
        while not rospy.is_shutdown():
            self.getDigitalLevel()
            self.get_GPS()
            self.raw_data = self.gpsData.strip() +", "+ str(self.x_slope) +",  "+  str(self.y_slope) +",  "+ str(self.x_level_temp) +",  "+ str(self.y_level_temp)
            # print(self.raw_data)
            self.pub.publish(self.raw_data)
            self.time_pub.publish(self.gpsDT)
            self.rate.sleep()


if __name__ == '__main__':
    rospy.init_node('read_rover_data')
    readData = ReadData()
    readData.send_data()
    # rospy.spin()
