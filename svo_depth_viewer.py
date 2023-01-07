import sys
import pyzed.sl as sl
import cv2
mouseX, mouseY = 500,500
def print_coordinates(event, x,y,flags,param):
    global mouseX, mouseY
    if event == cv2.EVENT_LBUTTONDOWN:
        mouseX, mouseY = x,y

def main():
    global mouseX, mouseY
    filepath = "C:\\Users\\Admin\\Documents\\ZED\\HD1080_SN14838_15-30-41_10.749m.svo"
    print("Reading SVO file: {0}".format(filepath))

    input_type = sl.InputType()
    input_type.set_from_svo_file(filepath)
    init = sl.InitParameters(input_t=input_type, svo_real_time_mode=False)
    cam = sl.Camera()
    status = cam.open(init)
    if status != sl.ERROR_CODE.SUCCESS:
        print(repr(status))
        exit()

    runtime = sl.RuntimeParameters()
    mat = sl.Mat()
    cv2.namedWindow('SVO Capture')
    cv2.setMouseCallback('SVO Capture', print_coordinates)
    key = ''
    while key != 113:  # for 'q' key
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
            print(depth_at_pixel)
            print(mouseX, mouseY)
            key = cv2.waitKey(1)
        else:
            key = cv2.waitKey(1)
    cv2.destroyAllWindows()


    cam.close()
    print("\nFINISH")




if __name__ == "__main__":
    main()