"""
GREEN - reference object
BLUE - moving object
"""

import sys
import cv2
import ogl_viewer.viewer as gl
import pyzed.sl as sl
import numpy as np
import math
import time

blue_lower_limit = np.array([85, 120, 40])  # setting the blue lower limit
blue_upper_limit = np.array([125, 255, 255])  # setting the blue upper limit
green_lower_limit = np.array([30, 100, 40])  # setting the green lower limit
green_upper_limit = np.array([102, 255, 255])  # setting the green upper limit
kernel = np.ones((3, 3), np.uint8)

pixel_cords_moving = (0, 0)
pixel_cords_ref = (0, 0)

if __name__ == "__main__":
    init = sl.InitParameters(camera_resolution=sl.RESOLUTION.HD720,
                                 depth_mode=sl.DEPTH_MODE.ULTRA,
                                 coordinate_units=sl.UNIT.METER,
                                 coordinate_system=sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP)
    zed = sl.Camera()
    status = zed.open(init)
    if status != sl.ERROR_CODE.SUCCESS:
        print(repr(status))
        exit()

    res = sl.Resolution()
    res.width = 1080
    res.height = 720

    camera_model = zed.get_camera_information().camera_model
    print(camera_model)

    point_cloud = sl.Mat(res.width, res.height, sl.MAT_TYPE.F32_C4, sl.MEM.CPU)
    image = sl.Mat(res.width, res.height, sl.MAT_TYPE.F32_C4, sl.MEM.CPU)

    viewer = gl.GLViewer()
    viewer.init(len(sys.argv), sys.argv, camera_model, res)
    while viewer.is_available():
        # Firstly, get coordinates of the objects
        if zed.grab() == sl.ERROR_CODE.SUCCESS:
            zed.retrieve_image(image, sl.VIEW.LEFT)

            image_cv2 = image.get_data()

            # Use HSV to easily get isolated colors
            image_hsv = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2HSV)
            mask_blue = cv2.inRange(image_hsv, blue_lower_limit, blue_upper_limit)
            mask_green = cv2.inRange(image_hsv, green_lower_limit, green_upper_limit)

            image_blue = cv2.bitwise_and(image_cv2, image_cv2, mask=mask_blue)
            image_green = cv2.bitwise_and(image_cv2, image_cv2, mask=mask_green)

            #cv2.imshow("Blue detection", image_blue)
            #cv2.imshow("Green detection", image_green)

            #Find center-weigth  of the blue object
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
                continue
            max_index = np.argmax(areas)
            largest_contour = contours[max_index]
            x1, y1, width, height = cv2.boundingRect(largest_contour)

            cv2.putText(image_blue, text="Moving object", org = (x1, y1 - 10), fontFace = cv2.FONT_HERSHEY_TRIPLEX,
                        fontScale=0.4, color=(0, 0, 255), thickness=1)
            cv2.rectangle(image_blue, (x1, y1), (x1 + width, y1 + height), (0, 255, 0), 2)
            cv2.circle(image_blue, (round(x1 + width / 2), round(y1 + height / 2)), 2, (0, 0, 255), 2)

            # Update coordinates of the moving object
            pixel_cords_moving = (round(x1 + width / 2), round(y1 + height / 2))

            #Find center-weigth  of the green object
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
                continue
            max_index = np.argmax(areas)
            largest_contour = contours[max_index]
            x1, y1, width, height = cv2.boundingRect(largest_contour)

            cv2.putText(image_green, text="Reference object", org=(x1, y1 - 10), fontFace=cv2.FONT_HERSHEY_TRIPLEX,
                        fontScale=0.4, color=(0, 0, 255), thickness=1)
            cv2.rectangle(image_green, (x1, y1), (x1 + width, y1 + height), (255, 0, 0), 2)
            cv2.circle(image_green, (round(x1 + width / 2), round(y1 + height / 2)), 2, (0, 0, 255), 2)
            # Update coordinates of the reference object
            pixel_cords_ref = (round(x1 + width / 2), round(y1 + height / 2))

            cv2.imshow("Combined image", image_blue + image_green)

            # Secondly, calculate distance
            zed.retrieve_measure(point_cloud, sl.MEASURE.XYZRGBA, sl.MEM.CPU, res)
            viewer.updateData(point_cloud)
            # Calculate distance from reference object to the moving object
            # Moving object
            point_moving_obj = point_cloud.get_value(pixel_cords_moving[0], pixel_cords_moving[1])
            x1 = point_moving_obj[1][0]
            y1 = point_moving_obj[1][1]
            z1 = point_moving_obj[1][2]

            # Reference object
            point_ref_obj = point_cloud.get_value(pixel_cords_ref[0], pixel_cords_ref[1])
            x2 = point_ref_obj[1][0]
            y2 = point_ref_obj[1][1]
            z2 = point_ref_obj[1][2]

            distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
            print(str(pixel_cords_ref) + "\t\t" + str(pixel_cords_moving))
            print("Distance: " + str(distance) + " meters")
        if cv2.waitKey(30) >= 0:
            break
    viewer.exit()
    zed.close()
