from matplotlib import pyplot as plt
from matplotlib import colors
from matplotlib.ticker import PercentFormatter
import numpy as np
import pyzed.sl as sl
import cv2
import math
import statistics
import datetime
import os

no_samples = 1000
coordinates = (0, 0)
real_measured_distance = 0.0
measurement_mode = 'QUALITY'
resolution_mode = 'HD1080'
'''
HD2K, HD1080,
HD720, VGA
'''
'''
Read for details on depth accuracy and best practices
https://www.stereolabs.com/docs/depth-sensing/depth-settings/
'''

def compute_data(data):
    global real_measured_distance
    global measurement_mode
    global resolution_mode

    current_date = datetime.datetime.now()
    folder_name = "m_" + current_date.strftime("%b-%d-%H-%M") + '_' + measurement_mode + '_' + resolution_mode
    os.mkdir("measurements/" + folder_name)

    # axis.hist()
    for i, measurement in enumerate(data):
        fig, axis = plt.subplots(figsize=(10, 5))
        N, bins, patches = axis.hist(measurement)  # , bins=[0, 0.02 ,0.05, 0.07, 0.10, 0.15, 0.20, 0.30, 0.40])

        # Setting color
        fracs = ((N ** (1 / 5)) / N.max())
        norm = colors.Normalize(fracs.min(), fracs.max())

        for thisfrac, thispatch in zip(fracs, patches):
            color = plt.cm.viridis(norm(thisfrac))
            thispatch.set_facecolor(color)

        plt.xlabel("Distance difference (m): Measured - Real")
        plt.ylabel("Measurements Taken")
        plt.title("Measurement {}".format(i + 1))
        plt.savefig("measurements/" + folder_name + "/measurement_{}.png".format(i))
        np.savetxt("measurements/" + folder_name + "/measurement_{}.csv".format(i), measurement, delimiter=',')
        plt.show()
        print("Median error of measurement {}: {}".format(i, statistics.median(measurement)))

    print("\nFinish")


def main():
    global no_samples
    global coordinates
    global real_measured_distance
    global measurement_mode
    global resolution_mode

    print('Running camera error calculations')

    # Create a ZED camera object
    zed = sl.Camera()

    # Set configuration parameters
    init = sl.InitParameters()
    init.camera_resolution = sl.RESOLUTION.HD1080

    if init.camera_resolution == sl.RESOLUTION.HD2K:
        resolution_mode = 'HD2K'
        init.camera_fps = 15
    elif init.camera_resolution == sl.RESOLUTION.HD1080:
        resolution_mode = 'HD1080'
        init.camera_fps = 30
    elif init.camera_resolution == sl.RESOLUTION.HD720:
        resolution_mode = 'HD720'
        init.camera_fps = 60
    elif init.camera_resolution == sl.RESOLUTION.VGA:
        resolution_mode = 'VGA'
        init.camera_fps = 100

    init.depth_mode = sl.DEPTH_MODE.QUALITY

    if init.depth_mode == sl.DEPTH_MODE.QUALITY:
        measurement_mode = 'QUALITY'
    elif init.depth_mode == sl.DEPTH_MODE.ULTRA:
        measurement_mode = 'ULTRA'
    init.depth_maximum_distance = 40
    init.coordinate_units = sl.UNIT.METER

    # Open the camera
    err = zed.open(init)
    if err != sl.ERROR_CODE.SUCCESS:
        zed.close()
        exit(1)

    # Set runtime parameters after opening the camera
    runtime = sl.RuntimeParameters()
    #runtime.sensing_mode = sl.SENSING_MODE.FILL
    runtime.sensing_mode = sl.SENSING_MODE.STANDARD

    # Prepare new image size to retrieve half-resolution images
    image_size = zed.get_camera_information().camera_resolution
    image_size.width = image_size.width / 2
    image_size.height = image_size.height / 2

    # Declare your sl.Mat matrices
    image_zed = sl.Mat(image_size.width, image_size.height, sl.MAT_TYPE.U8_C4)
    depth_image_zed = sl.Mat(image_size.width, image_size.height, sl.MAT_TYPE.U8_C4)
    depth_map = sl.Mat(image_size.width, image_size.height, sl.MAT_TYPE.U8_C4)

    # Measurements
    # Middle of the image
    coordinates = (round(image_size.width / 2), round(image_size.height / 2))

    data = []

    while True:
        temp_samples = no_samples
        real_measured_distance = float(input("Real measured distance to the object in meters:"))
        if real_measured_distance < 0:
            cv2.destroyAllWindows()
            zed.close()
            data = np.array(data)
            compute_data(data)
            return
        temp_measurements = []
        while temp_samples != 0:

            err = zed.grab(runtime)
            if err == sl.ERROR_CODE.SUCCESS:
                # Retrieve the left image, depth image in the half-resolution
                zed.retrieve_image(image_zed, sl.VIEW.LEFT, sl.MEM.CPU, image_size)
                zed.retrieve_image(depth_image_zed, sl.VIEW.DEPTH, sl.MEM.CPU, image_size)
                zed.retrieve_measure(depth_map, sl.MEASURE.DEPTH)

                image_cv2 = image_zed.get_data()
                depth_image_cv2 = depth_image_zed.get_data()

                measured_distance = depth_map.get_value(round(image_size.width / 2), round(image_size.height / 2))
                if math.isnan(measured_distance[1]) or math.isinf(measured_distance[1]):
                    continue
                text = "Distance: %.3f meters" % measured_distance[1]
                cv2.putText(depth_image_cv2, text=text, org=(20, 20),
                            fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=0.7, color=(0, 0, 255), thickness=1)
                cv2.circle(image_cv2, coordinates, 2, (0, 0, 255), 2)
                cv2.circle(depth_image_cv2, coordinates, 2, (0, 0, 255), 2)

                if not (math.isinf(measured_distance[1]) or math.isnan(measured_distance[1])):
                    temp_measurements.append(round(real_measured_distance - measured_distance[1], 3))

                # To recover data from sl.Mat to use it with opencv, use the get_data() method
                # It returns a numpy array that can be used as a matrix with opencv
                cv2.imshow("Image", image_cv2)
                cv2.imshow("Depth", depth_image_cv2)
                cv2.waitKey(10)
                temp_samples -= 1

        data.append(temp_measurements)


if __name__ == "__main__":
    main()
