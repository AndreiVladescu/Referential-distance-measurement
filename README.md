# Scope
This project aims to test the ZED and ZED2i cameras and integrate them with a UWB radar, for SAR imaging. This is the code for the WALLRAD IGARSS 2023 Article.

# Stereo camera
In the first part, I mostly used ZED. To get better results, we changed it with a ZED2i.

# Detection Mode
The camera firstly detects the objects of interest, blue and green balls, for which I have trained them using the YOLO v8 algorithm.
![Measured Objects](measured%20objects.png "Measured objects")

After the coordinates of the objects are collected, the computer than calculates the distance relative from one ball to the other. The radar is synchronised with it, using another platform, e.g. Raspberry Pi, hosting a socket server. The python client and C socket server then transfer the data from the Radar to the client.
