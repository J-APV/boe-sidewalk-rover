#!/usr/bin/env python

import rospy
import cv2, cv_bridge, numpy as np
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point, Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion
import math


class Follower:

    def __init__(self):
        self.bridge = cv_bridge.CvBridge()
        self.bocked = False
        self.locked = False
        self.target_angle = 0
        self.current_angle = 0
        self.move_angle = 0.2
        self.x = 0
        self.y = 0
        self.theta = 0
        # self.goal = Point()
        self.count = 0
        self.angular_speed = 2 * math.pi/180
        self.linear_speed = 0.1
        self.rate = rospy.Rate(0.1)
        self.scan_data = rospy.Subscriber('scan', LaserScan, self.scan_callback,queue_size=1)
        self.image_sub = rospy.Subscriber('camera/image_raw', Image, self.image_callback, queue_size=1)
        self.sub = rospy.Subscriber('wheel_odom', Odometry, self.odometry_callback, queue_size=1)
        self.cmd_vel_pub = rospy.Publisher('cmd_vel',Twist,queue_size=1)
        self.twist=Twist()

    def odometry_callback(self, msg):
        self.x = msg.pos.pose.position.x
        self.y = msg.pos.pose.position.y
        rot_q = msg.pos.pos.orientation
        (roll, pitch, self.theta) = euler_from_quaternion([rot_q.x, rot_q.y, rot_q.z, rot_q.w])
        print('x y theta', self.x, self.y, self.theta)

    def scan_callback(self, msg):
        if min(msg.ranges) < 0.7:
            self.blocked = True
        else:
            self.blocked = False

    def find_lower_upper_hsv(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        height, width, depth = image.shape
        # get the average HSV value of the sample segment
        rect_size = 1
        if (height < width):
            rect_size = int(height / 6)
        else:
            rect_size = int(width / 6)
        y_offset = int(height * (4 / 5))
        x_offset = int(width / 2) - int(rect_size / 2)
        temp_h = 0
        temp_s = 0
        temp_v = 0
        for y in range(rect_size):
            for x in range(rect_size):
                temp_h += (hsv[y + y_offset][x + x_offset])[0]
                temp_s += (hsv[y + y_offset][x + x_offset])[1]
                temp_v += (hsv[y + y_offset][x + x_offset])[2]
        temp_h /= rect_size * rect_size
        temp_s /= rect_size * rect_size
        temp_v /= rect_size * rect_size

        delta = 15
        if temp_h >= delta:
            low_h = temp_h - delta
        else:
            low_h = temp_h
        high_h = temp_h + delta

        if temp_s >= delta:
            low_s = temp_s - delta
        else:
            low_s = temp_s
        high_s = temp_s + delta

        if temp_v >= delta:
            low_v = temp_v - delta
        else:
            low_v = temp_v
        high_v = temp_v + delta

        lower_hsv = np.array([low_h, low_s, low_v], dtype=np.uint8)
        upper_hsv = np.array([high_h, high_s, high_v], dtype=np.uint8)

        return lower_hsv, upper_hsv


    # turn 10 degree per second
    def turn_rover(self, target_angle, clockwise):
        if clockwise:
            self.twist.angular.z = -abs(self.angular_speed)
        else:
            self.twist.angular.z = abs(self.angular_speed)
        self.twist.linear.x = 0
        t0 = rospy.Time.now().to_sec()
        current_angle = 0
        counter = 0
        rospy.sleep(1)
        while (not rospy.is_shutdown()) and (not self.blocked) and (current_angle < target_angle):
            # t1 = rospy.Time.now().to_sec()
            current_angle = self.angular_speed * (rospy.Time.now().to_sec() - t0)
            self.cmd_vel_pub.publish(self.twist)
            rospy.sleep(1)
            print('current angle', current_angle, 'counter', counter, 'x, y, theta', self.x, self.y, self.theta)
            counter += 1
        rospy.sleep(1)
        # stop the turn
        self.twist.linear.x = 0
        self.twist.angular.z = 0
        self.cmd_vel_pub.publish(self.twist)
        rospy.sleep(1)
        return current_angle, counter

    def drive_rover(self, distance):
        # send command to move
        self.twist.linear.x = self.linear_speed
        self.twist.angular.z = 0
        t0 = rospy.Time.now().to_sec()
        cur_distance = 0
        rospy.sleep(1)
        while (not rospy.is_shutdown()) and (not self.blocked) and (cur_distance < distance):
            cur_distance = self.linear_speed * (rospy.Time.now().to_sec() - t0)
            self.cmd_vel_pub.publish(self.twist)
            rospy.sleep(1)
            print('current distance', cur_distance)
        # stop the rover
        rospy.sleep(1)
        self.twist.linear.x = 0
        self.twist.angular.z = 0
        self.cmd_vel_pub.publish(self.twist)
        rospy.sleep(1)
        return cur_distance

    def image_callback(self, msg):
        image = self.bridge.imgmsg_to_cv2(msg,desired_encoding='bgr8')
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        height, width, depth = image.shape

        # find sample HSV color
        lower_hsv, upper_hsv = self.find_lower_upper_hsv(image)

        # Threshold the HSV image to get only sample colors
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)

        search_top = int(height * (3 / 4))
        search_bot = search_top + 30
        mask_hsv[0:search_top, 0:width] = 0
        mask_hsv[search_bot:0, 0:width] = 0
        M = cv2.moments(mask_hsv)
        cx = 0
        cy = 0
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            # cv2.circle(image, (cx, cy), 5, (0, 0, 255), -1)
        # camera of leo rover is not in the center. add offset of 100 pixel to adjust camera position
        err = (cx - (width - 100) /2)
        dy = height - cy
        d = np.sqrt(err * err + dy * dy)
        self.target_angle = np.arccos(dy / d)
        self.relative_angle = 0

        cw = True
        if((err>0)):
            cw = True
        else:
            cw = False
        # if the angle is less than 10 degree, do not move rover
        if (not rospy.is_shutdown()) and (not self.blocked) and (not self.locked) and (self.target_angle > (math.pi/(18))):
            self.locked = True
            # turn half of target angle
            self.relative_angle, counter  = self.turn_rover(self.move_angle, cw)
            # move 20 cm at a time
            self.drive_rover(0.2)
            # return the angle to set the right heading position
            # self.target_angle, counter = self.turn_rover(self.relative_angle, not (cw))
        else:
            self.locked = True
            self.drive_rover(0.2)
        rospy.sleep(1)

        self.locked = False
        print('height, width', height, width, 'cx cy', cx, cy, 'err', err, 'dy', dy, 'd', d, 'degree',
              self.target_angle, self.target_angle * (180 / math.pi), self.relative_angle)
        self.rate.sleep()
        self.target_angle = 0


if __name__ == '__main__':
    rospy.init_node('follower')
    follower = Follower()
    rospy.spin()