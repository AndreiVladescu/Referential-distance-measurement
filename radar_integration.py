import math

import pyzed.sl as sl
import cv2
import socket
import struct
import numpy as np
from ultralytics import YOLO
import supervision as sv

mobile_platform_ip = '192.168.0.203'
mobile_platform_port = 12345

blue_lower_limit = np.array([85, 120, 50])  # setting the blue lower limit
blue_upper_limit = np.array([125, 255, 255])  # setting the blue upper limit
green_lower_limit = np.array([30, 80, 20])  # setting the green lower limit
green_upper_limit = np.array([102, 255, 255])  # setting the green upper limit

s = socket.socket()

model = YOLO("best.pt");
box_an = sv.BoxAnnotator(
    thickness=2,
    text_thickness=2,
    text_scale=1
)
def color_mask(image_cv2, point_cloud):
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
    full_image = image_blue + image_green

    # Calculate distance from reference object to the moving object

    # Moving object
    point_moving_obj = point_cloud.get_value(pixel_cords_moving[0], pixel_cords_moving[1])
    moving_x1 = point_moving_obj[1][0]
    moving_y1 = point_moving_obj[1][1]
    moving_z1 = point_moving_obj[1][2]

    # Reference object
    point_static_obj = point_cloud.get_value(pixel_cords_static[0], pixel_cords_static[1])
    static_x2 = point_static_obj[1][0]
    static_y2 = point_static_obj[1][1]
    static_z2 = point_static_obj[1][2]

    distance = math.sqrt((moving_x1 - static_x2) ** 2 + (moving_y1 - static_y2) ** 2 + (moving_z1 - static_z2) ** 2)

    # Distance lower than 0.06 are runt frames
    if np.isnan(distance) or np.isinf(distance):
        distance = -1

    text = "Distance: %.3f milimeters" % distance
    cv2.putText(full_image, text=text, org=(5, 20), fontFace=cv2.FONT_HERSHEY_TRIPLEX,
                fontScale=0.8, color=(128, 192, 0), thickness=1)

    return full_image, distance


def get_radar_data():
    global s

    s.send(b"1")
    data = s.recv(4)
    data = struct.unpack('<i', data)[0]
    print("Received from server: {0}".format(data))
    num_samples = data

    i = 0
    radar_data_array = []
    while i < num_samples:
        data = s.recv(4)
        data = struct.unpack('<i', data)[0]
        print(data)
        radar_data_array.append(data)
        i = i + 1

    print(radar_data_array)


def yolo_filter(frame):
    result = model(frame)[0]

    detections = sv.Detections.from_yolov8(result)
    frame = box_an.annotate(scene=frame, detections=detections)
    black_img = np.zeros_like(frame)

    boxes = detections.xyxy.astype(int)

    for box in boxes:
        x1, y1, x2, y2 = box
        black_img[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

    return black_img

def main():
    global s

    s.connect((mobile_platform_ip, mobile_platform_port))

    zed = sl.Camera()
    init = sl.InitParameters()

    init.camera_resolution = sl.RESOLUTION.HD1080
    init.camera_fps = 30
    init.depth_mode = sl.DEPTH_MODE.PERFORMANCE
    init.coordinate_units = sl.UNIT.MILLIMETER

    err = zed.open(init)
    if err != sl.ERROR_CODE.SUCCESS:
        print(repr(err))
        zed.close()
        exit(1)

    runtime = sl.RuntimeParameters()
    runtime.sensing_mode = sl.SENSING_MODE.STANDARD

    image_size = zed.get_camera_information().camera_resolution
    image_size.width = image_size.width / 2
    image_size.height = image_size.height / 2

    coordinates = (int(image_size.width / 2), int(image_size.height / 2))

    image_zed = sl.Mat(image_size.width, image_size.height, sl.MAT_TYPE.U8_C4)
    point_cloud = sl.Mat()

    key = ' '
    while key != 113:
        err = zed.grab(runtime)
        if err == sl.ERROR_CODE.SUCCESS:
            zed.retrieve_image(image_zed, sl.VIEW.LEFT, sl.MEM.CPU, image_size)

            zed.retrieve_measure(point_cloud, sl.MEASURE.XYZRGBA, sl.MEM.CPU, image_size)
            print('Distance to center:{0}'.format(point_cloud.get_value(coordinates[0], coordinates[1])[1][2]))
            image_ocv = image_zed.get_data()

            image_filtered = yolo_filter(image_ocv)

            image_masked, distance = color_mask(image_filtered, point_cloud)

            cv2.imshow("Masked Image", image_masked)
            cv2.imshow("Original Image", image_ocv)

            get_radar_data()

            key = cv2.waitKey(0)

            if key == 99:
                print('Capturing frame')
            elif key == 105:
                print('Ignoring frame')
            else:
                print('Key not a command, skipping...')



    cv2.destroyAllWindows()
    zed.close()
    s.send(b"0")
    s.close()


if __name__ == "__main__":
    main()
