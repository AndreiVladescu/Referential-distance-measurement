# Referential-distance-measurement
Stereo-camera distance measurement between 2 objects: green (the reference object) and blue (the supposed moving object)

# Stereo camera
In this project I used the ZED 1 Stereo Camera with the ZED SDK https://www.stereolabs.com/. The camera is static.
I used 1080 x 720p resolution to get decent framerate and the depth_mode is set on ULTRA

# Detection Mode
Firstly, an image is taken on the left camera to get the center of the rectangle encapsulating the 2 objects.
Secondly, the point cloud feature is used to get X,Y and Z coordinates of each of the pixels. 
The distance between is then calculated by using the formula of distance between 2 points in space: sqrt(Δx**2 + Δy**2 + Δz**2).
