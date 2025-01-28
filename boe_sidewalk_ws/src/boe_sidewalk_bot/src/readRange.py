#!/usr/bin/env python3

import rospy
from std_msgs.msg import String
from std_msgs.msg import Int16
from std_msgs.msg import Float64
from sensor_msgs.msg import Range
from geometry_msgs.msg import Twist
from collections import deque
# import datetime as time


SIZE = 5

class ReceiveRange:
    def __init__(self):
        self.msg_sub = []
        self.measurements_queue = deque(maxlen=10)
        self.rate = rospy.Rate(1)
        for x in range(1, 4):
           self.msg_sub.append(rospy.Subscriber("/pi_sonar/sonar_" + str(3), Range, self.collect_data_callback, callback_args=str(3)))
        self.msg_pub = rospy.Publisher('is_safe', Int16, queue_size=1)
        self.avg_pub = rospy.Publisher('avg_distance', Float64, queue_size=1)
        self.speed_pub = rospy.Publisher('current_speed', Float64, queue_size=1)
        self.msg_speed_sub = rospy.Subscriber("/cmd_vel", Twist, self.collect_speed_callback)
        self.msg = 1
        self.avg_measurement = 0.0
        self.speed = 0.0
        
        self.safe_distance = 0.7

    def collect_data_callback(self, msg, sonarNumber):
        #print("Sonar " + sonarNumber)
        #print(" received - ", msg.range)	
        self.measurements_queue.append(msg.range)
        print(len(self.measurements_queue))
        if len(self.measurements_queue) == self.measurements_queue.maxlen:
            self.avg_measurement = sum(self.measurements_queue) / self.measurements_queue.maxlen
            print("avg measurement" + str(self.avg_measurement))
            if self.avg_measurement > self.safe_distance:
               self.msg = 1
            else:
               self.msg = 0
        
        
        #self.rate.sleep()

    def collect_speed_callback(self, msg):
        #print("current speed of rover is ", msg.linear.x)
        self.speed = msg.linear.x
        #self.rate.sleep()

    def send_msg(self):
        while not rospy.is_shutdown():
            self.msg_pub.publish(self.msg)
            self.avg_pub.publish(self.avg_measurement)
            self.speed_pub.publish(self.speed)
            #self.rate.sleep()
    

if __name__ == '__main__':
    rospy.init_node('receive_range_data')
    receiveRange = ReceiveRange()
    receiveRange.send_msg()
    rospy.spin()
