#!/usr/bin/env python

import rospy
from std_msgs.msg import String
import datetime as time

class ReceiveMSG:
    def __init__(self):
        self.msg_pub = rospy.Subscriber('my_msg', String, self.collect_data_callback)
        self.rate = rospy.Rate(1)

    def collect_data_callback(self, msg):
        print("received - ", msg.data)
        self.rate.sleep()


if __name__ == '__main__':
    rospy.init_node('receive_sample_data')
    receiveMSG = ReceiveMSG()
    rospy.spin()
