#!/usr/bin/env python

import rospy
from std_msgs.msg import String
from std_msgs.msg import Int16
from std_msgs.msg import Int32
import datetime as time



class SaveData:
    def __init__(self):
        self.rover_data = []
        self.datasub = rospy.Subscriber('rover_data', String, self.collectDataCallback)
        self.statussub = rospy.Subscriber('start_val', Int16, self.collectStartStatusCallback)
        self.sidsub = rospy.Subscriber('section_id', String, self.collectSidewalkIDCallback)
        self.curr_timesub = rospy.Subscriber('current_time', String, self.setTimeCallback)
        self.counterpub = rospy.Publisher('rover_data_counter', Int32 , queue_size=1)
        self.max_count = 100
        self.count = 0
        self.filecount = 0
        self.numofRecords= 0
        self.start_status = False
        self.pre_section_id = "000"
        self.section_id = "000"
        self.setInit_section_id = True
        self.curr_time = ""
        self.rate = rospy.Rate(1)

    def collectDataCallback(self, msg):
        if(self.start_status):
            data = self.section_id + ", " + msg.data
            self.rover_data.append(data)
            self.count += 1
            if (self.pre_section_id == self.section_id):
                self.numofRecords += 1
            else:
                self.pre_section_id = self.section_id
                self.numofRecords = 1
            self.counterpub.publish(self.numofRecords)
            self.rate.sleep()

        if (self.count == self.max_count):
            self.count = 0
            self.save_data()
        # end of data collection. save the leftover data
        if(not (self.start_status) and (self.count>0)):
            self.count = 0
            self.save_data()

    def collectSidewalkIDCallback(self, msg):
        if(not self.setInit_section_id):
            self.section_id = msg.data
        else:
            self.section_id = msg.data
            self.pre_section_id = msg.data
            self.setInit_section_id = False

    def setTimeCallback(self, msg):
        self.curr_time = msg.data

    def collectStartStatusCallback(self, msg):
        # print(msg.data)
        if (msg.data > 0 ):
            self.start_status = True
        else:
            self.start_status = False
            # self.numofRecords = 0

    def save_data(self):
        # self.filecount += 1
        print(len(self.rover_data), "Saving data...")
        t = time.datetime.today()
        name = "/home/pi/data/" + self.curr_time + "_slope_data.csv"
        # name = "/home/pi/data/"   + t.strftime("%Y_%m_%d_%H_%M_%S") + "_slope_data.csv"
        with open(name, mode='w') as datafile:
            while(len(self.rover_data)>0):
                # print(self.rover_data[-1])
                datafile.write(self.rover_data.pop(0) + "\n")

if __name__ == '__main__':
    rospy.init_node('save_rover_data')
    saveData = SaveData()
    rospy.spin()


