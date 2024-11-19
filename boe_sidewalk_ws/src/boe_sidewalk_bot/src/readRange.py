#!/usr/bin/env python3

import rospy
from std_msgs.msg import String
from std_msgs.msg import Int16
from sensor_msgs.msg import Range
from geometry_msgs.msg import Twist
# import datetime as time


SIZE = 5

class ReceiveRange:
    def __init__(self):
        self.msg_sub = []
        self.rate = rospy.Rate(1)
        for x in range(SIZE):
            self.msg_sub.append(rospy.Subscriber("/pi_sonar/sonar_" + str(x), Range, self.collect_data_callback))
        self.msg_pub = rospy.Publisher('is_safe', Int16, queue_size=1)
        self.msg_speed_sub = rospy.Subscriber("/cmd_vel", Twist, self.collect_speed_callback)
        self.msg = 1
        self.safe_distance = 2

    def collect_data_callback(self, msg):
        print("received - ", msg.range)
        if msg.range > self.safe_distance:
            self.msg = 1
        else:
            self.msg = 0
        self.rate.sleep()

    def collect_speed_callback(self, msg):
        print("current speed of rober is ", msg.linear.x)
        self.rate.sleep()

    def send_msg(self):
        while not rospy.is_shutdown():
            self.msg_pub.publish(self.msg)
            self.rate.sleep()


if __name__ == '__main__':
    rospy.init_node('receive_range_data')
    receiveRange = ReceiveRange()
    receiveRange.send_msg()
    rospy.spin()
