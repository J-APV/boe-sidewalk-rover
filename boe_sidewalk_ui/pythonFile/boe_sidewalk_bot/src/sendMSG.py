#!/usr/bin/env python

import rospy
from std_msgs.msg import String
import datetime as time

class SendMSG:
    def __init__(self):
        self.msg_pub = rospy.Publisher('my_msg', String, queue_size = 1)
        self.rate = rospy.Rate(1)
        self.msg = ""
        self.counter = 0

    def get_msg(self):
        self.counter += 1
        self.msg = "How are you?" + str(self.counter)

    def send_msg(self):
        while not rospy.is_shutdown():
            self.get_msg()
            self.msg_pub.publish(self.msg)
            self.rate.sleep()

if __name__ == '__main__':
    rospy.init_node('send_sample_data')
    sendMSG = SendMSG()
    sendMSG.send_msg()

