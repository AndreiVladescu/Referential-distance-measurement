import pyzed.sl as sl
import cv2
import numpy as np
import threading
import time
import signal
import math
import sys
from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt

zed_list = []
left_list = []
depth_list = []
timestamp_list = []
thread_list = []
stop_signal = False

full_image_list = []
distance_list = []
point_cloud_list = []
x_cords_list = []
y_cords_list = []
z_cords_list = []

blue_lower_limit = np.array([85, 120, 50])  # setting the blue lower limit
blue_upper_limit = np.array([125, 255, 255])  # setting the blue upper limit
green_lower_limit = np.array([30, 80, 20])  # setting the green lower limit
green_upper_limit = np.array([102, 255, 255])  # setting the green upper limit

file_name = "distances.txt"
show_camera_feed = False
show_camera_feed_masked = True
measurements_limit = 2500
measurements_index = 0

def signal_handler(signal, frame):
    global stop_signal
    stop_signal = True
    time.sleep(0.5)
    exit()


def grab_run(index):
    global stop_signal
    global zed_list
    global timestamp_list
    global left_list
    global depth_list
    global full_image_list
    global distance_list
    global point_cloud_list
    global x_cords_list
    global y_cords_list
    global z_cords_list
    global measurements_index
    global measurements_limit

    runtime = sl.RuntimeParameters()
    while not stop_signal:
        err = zed_list[index].grab(runtime)
        if err == sl.ERROR_CODE.SUCCESS:
            zed_list[index].retrieve_image(left_list[index], sl.VIEW.LEFT)
            #zed_list[index].retrieve_measure(depth_list[index], sl.MEASURE.DEPTH)
            zed_list[index].retrieve_measure(point_cloud_list[index], sl.MEASURE.XYZ, sl.MEM.CPU)
            timestamp_list[index] = zed_list[index].get_timestamp(sl.TIME_REFERENCE.CURRENT).data_ns
            find_center_weights(index)
            measurements_index += 1
        time.sleep(0.005)  # 5ms
    zed_list[index].close()



# Getting the coordinates
def find_center_weights(index):
    global zed_list
    global left_list
    global depth_list
    global full_image_list
    global distance_list
    global point_cloud_list
    global x_cords_list
    global y_cords_list
    global z_cords_list

    # Use image of the left camera
    image_cv2 = left_list[index].get_data()

    # Use HSV to easily get isolated colors
    image_hsv = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2HSV)
    mask_blue = cv2.inRange(image_hsv, blue_lower_limit, blue_upper_limit)
    mask_green = cv2.inRange(image_hsv, green_lower_limit, green_upper_limit)

    image_blue = cv2.bitwise_and(image_cv2, image_cv2, mask=mask_blue)
    image_green = cv2.bitwise_and(image_cv2, image_cv2, mask=mask_green)

    # Find center-weight  of the blue object
    gray = cv2.cvtColor(image_blue, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    gray = cv2.erode(gray, (5, 5), cv2.BORDER_REFLECT)
    gray = cv2.dilate(gray, (6, 6), cv2.BORDER_REFLECT)
    ret, gray = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)

    edged = cv2.Canny(gray, 30, 255)
    edged = cv2.dilate(edged, (4, 4), cv2.BORDER_REFLECT)

    contours, hierarchy = cv2.findContours(edged,
                                           cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    areas = [cv2.contourArea(temp) for temp in contours]
    if len(areas) == 0:
        return
    max_index = np.argmax(areas)
    largest_contour = contours[max_index]
    x_moving, y_moving, width, height = cv2.boundingRect(largest_contour)

    cv2.putText(image_blue, text="Moving object", org=(x_moving, y_moving - 10), fontFace=cv2.FONT_HERSHEY_TRIPLEX,
                fontScale=0.5, color=(0, 0, 255), thickness=1)
    cv2.rectangle(image_blue, (x_moving, y_moving), (x_moving + width, y_moving + height), (0, 255, 0), 2)
    cv2.circle(image_blue, (round(x_moving + width / 2), round(y_moving + height / 2)), 2, (0, 0, 255), 2)

    # Update coordinates of the moving object
    pixel_cords_moving = (round(x_moving + width / 2), round(y_moving + height / 2))

    # Find center-weigth  of the green object
    gray = cv2.cvtColor(image_green, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    gray = cv2.erode(gray, (5, 5), cv2.BORDER_REFLECT)
    gray = cv2.dilate(gray, (6, 6), cv2.BORDER_REFLECT)
    ret, gray = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)

    edged = cv2.Canny(gray, 30, 255)
    edged = cv2.dilate(edged, (4, 4), cv2.BORDER_REFLECT)

    contours, hierarchy = cv2.findContours(edged,
                                           cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    areas = [cv2.contourArea(temp) for temp in contours]
    if len(areas) == 0:
        return
    max_index = np.argmax(areas)
    largest_contour = contours[max_index]
    x_static, y_static, width, height = cv2.boundingRect(largest_contour)

    cv2.putText(image_green, text="Static object", org=(x_static, y_static - 10), fontFace=cv2.FONT_HERSHEY_TRIPLEX,
                fontScale=0.5, color=(0, 0, 255), thickness=1)
    cv2.rectangle(image_green, (x_static, y_static), (x_static + width, y_static + height), (255, 0, 0), 2)
    cv2.circle(image_green, (round(x_static + width / 2), round(y_static + height / 2)), 2, (0, 0, 255), 2)
    # Update coordinates of the reference object
    pixel_cords_static = (round(x_static + width / 2), round(y_static + height / 2))

    # Calculate distance from reference object to the moving object
    # Moving object
    point_moving_obj = point_cloud_list[index].get_value(pixel_cords_moving[0], pixel_cords_moving[1])
    moving_x1 = point_moving_obj[1][0]
    moving_y1 = point_moving_obj[1][1]
    moving_z1 = point_moving_obj[1][2]

    # Reference object
    point_static_obj = point_cloud_list[index].get_value(pixel_cords_static[0], pixel_cords_static[1])
    static_x2 = point_static_obj[1][0]
    static_y2 = point_static_obj[1][1]
    static_z2 = point_static_obj[1][2]

    distance = math.sqrt((moving_x1 - static_x2) ** 2 + (moving_y1 - static_y2) ** 2 + (moving_z1 - static_z2) ** 2)

    # Distance lower than 0.06 are runt frames
    if distance <= 0.06 or np.isnan(distance):
        return

    #print("Estimated distance between the 2 objects: " + str(distance) + " meters")
    distance_list[index] = distance

    full_image = image_blue + image_green
    text = "Distance: %.3f meters" % distance
    cv2.putText(full_image, text=text, org=(5, 20), fontFace=cv2.FONT_HERSHEY_TRIPLEX,
                fontScale=0.8, color=(128, 192, 0), thickness=1)
    full_image_list[index] = full_image

    x_cords_list[index] = moving_x1 - static_x2
    y_cords_list[index] = moving_y1 - static_y2
    z_cords_list[index] = moving_z1 - static_z2

def print_distances_to_file(index, output_file):
    global distance_list
    output_file.write(str(distance_list[index]) + '\n')

def main():
    global stop_signal
    global zed_list
    global left_list
    global depth_list
    global timestamp_list
    global thread_list
    global full_image_list
    global distance_list
    global point_cloud_list
    global x_cords_list
    global y_cords_list
    global z_cords_list
    global show_camera_feed
    global show_camera_feed_masked
    global measurements_limit
    global measurements_index

    output_file = open(file_name, "w")

    signal.signal(signal.SIGINT, signal_handler)

    print("Running...")
    init = sl.InitParameters()
    init.camera_resolution = sl.RESOLUTION.HD720
    init.camera_fps = 30  # The framerate is lowered to avoid any USB3 bandwidth issues
    init.coordinate_units = sl.UNIT.METER
    init.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP

    # List and open cameras
    name_list = []
    last_ts_list = []
    cameras = sl.Camera.get_device_list()
    index = 0
    for cam in cameras:
        init.set_from_serial_number(cam.serial_number)
        name_list.append("ZED {}".format(cam.serial_number))
        print("Opening {}".format(name_list[index]))
        zed_list.append(sl.Camera())
        left_list.append(sl.Mat())
        depth_list.append(sl.Mat())
        point_cloud_list.append(sl.Mat())
        timestamp_list.append(0)
        last_ts_list.append(0)
        full_image_list.append(0)
        distance_list.append(0)
        x_cords_list.append(0)
        y_cords_list.append(0)
        z_cords_list.append(0)

        status = zed_list[index].open(init)
        if status != sl.ERROR_CODE.SUCCESS:
            print(repr(status))
            zed_list[index].close()
        index = index + 1

    # Start camera threads
    for index in range(0, len(zed_list)):
        if zed_list[index].is_opened():
            thread_list.append(threading.Thread(target=grab_run, args=(index,)))
            thread_list[index].start()

    # Display camera images
    key = ''
    while key != 113:  # for 'q' key
        if measurements_index > measurements_limit:
            break
        for index in range(0, len(zed_list)):
            if zed_list[index].is_opened():

                if (timestamp_list[index] > last_ts_list[index]):

                    if show_camera_feed_masked:
                        cv2.namedWindow('Masked image from {}'.format(name_list[index]), cv2.WINDOW_NORMAL)
                        cv2.imshow('Masked image from {}'.format(name_list[index]), full_image_list[index])
                        cv2.resizeWindow('Masked image from {}'.format(name_list[index]), 1366, 720)

                    if show_camera_feed:
                        cv2.imshow(name_list[index], left_list[index].get_data())


                    print("Measure from {}: ".format(name_list[index]) + str(distance_list[index]) + " meters")
                    print_distances_to_file(index, output_file)

                    median_distance = 0
                    median_cords = [0, 0, 0]

                    for distance_index in range(0, len(distance_list)):
                        median_distance += distance_list[distance_index]
                    median_distance = median_distance / len(zed_list)
                    if index == 0:
                        print("Median distance between the 2 objects: " + str(median_distance) + " meters\n")

                    for cords_index in range(0, len(x_cords_list)):
                        median_cords[0] += x_cords_list[cords_index] / len(x_cords_list)
                        median_cords[1] += y_cords_list[cords_index] / len(y_cords_list)
                        median_cords[2] += z_cords_list[cords_index] / len(z_cords_list)
                    if index == 0:
                        print("Coordinates from origin to moving: (x, y, z) " + str(median_cords[0]) + " "
                              + str(median_cords[1]) + " " + str(median_cords[2]))
                    last_ts_list[index] = timestamp_list[index]

        key = cv2.waitKey(10)

    cv2.destroyAllWindows()

    # Stop the threads
    stop_signal = True
    for index in range(0, len(thread_list)):
        thread_list[index].join()

    output_file.close()
    print("\nProgram Finished")


if __name__ == "__main__":
    main()