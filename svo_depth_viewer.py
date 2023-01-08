import datetime
import math
import os
import statistics
import sys

import numpy as np
import pyzed.sl as sl
import cv2
from matplotlib import pyplot as plt, colors

mouseX, mouseY = -1, -1
def print_coordinates(event, x,y,flags,param):
    global mouseX, mouseY
    if event == cv2.EVENT_LBUTTONDOWN:
        mouseX, mouseY = x,y
        print(mouseX, mouseY)

def rmse(predictions, actuals):
  diff = [(p - a) ** 2 for p, a in zip(predictions, actuals)]
  return math.sqrt(statistics.mean(diff))

def compute_data(data, file_name, real_measured_distance):
    rmse_vector = [0 for _ in range(len(data))]
    if file_name.find('day') > 0:
        day_cycle = 'day'
    else:
        day_cycle = 'night'
    file_name = file_name[:file_name.find('m')]
    current_date = datetime.datetime.now()
    folder_name = "SVO_" + current_date.strftime("%b-%d-%H-%M") + '_' + file_name + '_' + day_cycle
    os.mkdir("measurements/" + folder_name)

    fig, axis = plt.subplots(figsize=(10, 5))
    N, bins, patches = axis.hist(data)
    # Setting color
    fracs = ((N ** (1 / 5)) / N.max())
    norm = colors.Normalize(fracs.min(), fracs.max())

    for thisfrac, thispatch in zip(fracs, patches):
        color = plt.cm.viridis(norm(thisfrac))
        thispatch.set_facecolor(color)

    plt.xlabel("Distance difference (m): Real - Measured")
    plt.ylabel("Measurements Taken")
    plt.title("Measurement {}".format(real_measured_distance))
    plt.savefig("measurements/" + folder_name + "/measurement.png")
    np.savetxt("measurements/" + folder_name + "/measurement.csv", data, delimiter=',')

    np.savetxt("measurements/" + folder_name + "/errors.txt", [statistics.median(data), rmse(data, rmse_vector)], delimiter=',')
    plt.show()
    print("Median error of measurement: {}".format(statistics.median(data)))
    print("RMSE: {}".format(rmse(data, rmse_vector)))

def main():
    global mouseX, mouseY
    file_name = '20.070m_night.svo'
    real_measured_distance = float('%.3f' % float(file_name[:file_name.find('m')]))
    dir_path = "D:\\Documents\\Fisiere\\Research\\IGARSS\\Good data\\"
    filepath = dir_path + file_name
    print("Reading SVO file: {0}".format(filepath))

    input_type = sl.InputType()
    input_type.set_from_svo_file(filepath)
    init = sl.InitParameters(input_t=input_type, svo_real_time_mode=False)
    init.depth_mode = sl.DEPTH_MODE.QUALITY

    runtime = sl.RuntimeParameters()
    runtime.sensing_mode = sl.SENSING_MODE.STANDARD
    cam = sl.Camera()
    status = cam.open(init)
    if status != sl.ERROR_CODE.SUCCESS:
        print(repr(status))
        exit()

    runtime = sl.RuntimeParameters()
    mat = sl.Mat()
    cv2.namedWindow('SVO Capture')
    cv2.setMouseCallback('SVO Capture', print_coordinates)

    err = cam.grab(runtime)
    if err == sl.ERROR_CODE.SUCCESS:
        cam.retrieve_image(mat)
        img = mat.get_data()
        cv2.circle(img, (mouseX, mouseY), 1, (0, 0, 255), -1)
        cv2.imshow("SVO Capture", img)
        depth = sl.Mat()
        cam.retrieve_measure(depth, sl.MEASURE.DEPTH)
        depth_data = depth.get_data()
        while mouseX < 0:
            cv2.waitKey(1)
        depth_at_pixel = depth_data[mouseY, mouseX]
        print(depth_at_pixel)

    data = []
    count = 1000
    while count:  # for 'q' key
        err = cam.grab(runtime)
        if err == sl.ERROR_CODE.SUCCESS:
            cam.retrieve_image(mat)
            img = mat.get_data()
            cv2.circle(img, (mouseX, mouseY), 1, (0, 0, 255), -1)
            cv2.imshow("SVO Capture", img)
            depth = sl.Mat()
            cam.retrieve_measure(depth, sl.MEASURE.DEPTH)
            depth_data = depth.get_data()
            depth_at_pixel = depth_data[mouseY, mouseX]
            depth_at_pixel /= 1000
            if math.isnan(depth_at_pixel) or math.isinf(depth_at_pixel):
                continue
            data.append(round(real_measured_distance - depth_at_pixel, 3))
            print(depth_at_pixel)
            count -= 1
            cv2.waitKey(1)

    cv2.destroyAllWindows()
    cam.close()

    compute_data(data, file_name, real_measured_distance)

if __name__ == "__main__":
    main()