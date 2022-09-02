from matplotlib import pyplot as plt
from matplotlib import colors
from matplotlib.ticker import PercentFormatter
import numpy as np
import pyzed.sl as sl
import cv2
import math

no_samples = 1000
# Optional, leave 0 if not used
real_measured_distance = 1.96
coordinates = (0, 0)

'''
Read for details on depth accuracy and best practices
https://www.stereolabs.com/docs/depth-sensing/depth-settings/
'''

def main():
    global no_samples
    global real_measured_distance
    global coordinates

    print('Running camera error calculations')

    # Create a ZED camera object
    zed = sl.Camera()

    # Set configuration parameters
    init = sl.InitParameters()
    init.camera_resolution = sl.RESOLUTION.HD1080
    init.depth_mode = sl.DEPTH_MODE.QUALITY
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

    key = ''
    while key != 113:  # for 'q' key
        if no_samples == 0:
            break
        no_samples -= 1
        err = zed.grab(runtime)
        if err == sl.ERROR_CODE.SUCCESS:
            # Retrieve the left image, depth image in the half-resolution
            zed.retrieve_image(image_zed, sl.VIEW.LEFT, sl.MEM.CPU, image_size)
            zed.retrieve_image(depth_image_zed, sl.VIEW.DEPTH, sl.MEM.CPU, image_size)
            zed.retrieve_measure(depth_map, sl.MEASURE.DEPTH)

            image_cv2 = image_zed.get_data()
            depth_image_cv2 = depth_image_zed.get_data()

            measured_distance = depth_map.get_value(round(image_size.width / 2), round(image_size.height / 2))
            text = "Distance: %.3f meters" % measured_distance[1]
            cv2.putText(depth_image_cv2,
                        text = text, org=(20, 20),
                        fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=0.5, color=(0, 0, 255), thickness=1)
            cv2.circle(image_cv2, coordinates, 2, (0, 0, 255), 2)
            cv2.circle(depth_image_cv2, coordinates, 2, (0, 0, 255), 2)
            if not math.isinf(measured_distance[1]):
                if real_measured_distance != 0:
                    data.append(round(measured_distance[1] - real_measured_distance, 3))
                else:
                    data.append(round(measured_distance[1], 3))
            # To recover data from sl.Mat to use it with opencv, use the get_data() method
            # It returns a numpy array that can be used as a matrix with opencv

            cv2.imshow("Image", image_cv2)
            cv2.imshow("Depth", depth_image_cv2)

        key = cv2.waitKey(10)

    cv2.destroyAllWindows()
    zed.close()

    data = np.array(data)
    fig, axis = plt.subplots(figsize= (10, 5))
    N, bins, patches = axis.hist(data)

    # Setting color
    fracs = ((N ** (1 / 5)) / N.max())
    norm = colors.Normalize(fracs.min(), fracs.max())

    for thisfrac, thispatch in zip(fracs, patches):
        color = plt.cm.viridis(norm(thisfrac))
        thispatch.set_facecolor(color)

    if real_measured_distance != 0:
        plt.xlabel("Distance difference")
    else:
        plt.xlabel("Measured distance")
    plt.ylabel("Measurements Taken")
    plt.show()

    print("\nFinish")

if __name__ == "__main__":
    main()
