import pyzed.sl as sl
import cv2
import numpy as np
import threading
import time
import signal
import math
import sys
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt

mobile_platform_ip = '192.168.0.230'
mobile_platform_port = 5678

def main() :
    zed = sl.Camera()

    init = sl.InitParameters()

    init.camera_resolution = sl.RESOLUTION.HD1080
    init.depth_mode = sl.DEPTH_MODE.QUALITY
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

            image_ocv = cv2.circle(image_ocv, coordinates, 1, (0, 0, 255), 2)

            cv2.imshow("Image", image_ocv)

            key = cv2.waitKey(1)
            if key == 99:
                print('Capturing frame')
            elif key == 105:
                print('Ignoring frame')
            else:
                print('Key not a command, skipping...')

            '''
            cod pentru captura socket si afisare in consola output de la rpi/radar
            '''

    cv2.destroyAllWindows()
    zed.close()

if __name__ == "__main__":
    main()