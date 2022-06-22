# Referential-distance-measurement
Stereo-camera distance measurement between 2 objects: green (the reference object) and blue (the supposed moving object)

# Stereo camera
In this project I used the ZED 1 Stereo Camera with the ZED SDK https://www.stereolabs.com/. The camera is static.
I used 1080 x 720p resolution to get decent framerate and the depth_mode is set on ULTRA

# Detection Mode
Firstly, an image is taken on the left camera to get the center of the rectangle encapsulating the 2 objects.
Secondly, the point cloud feature is used to get X,Y and Z coordinates of each of the pixels. 
The distance between is then calculated by using the formula of distance between 2 points in space: sqrt(Δx**2 + Δy**2 + Δz**2).

# Photos

What the point cloud looks like
![Photo](https://github.com/AndreiVladescu/Referential-distance-measurement/blob/main/photo1.png?raw=true)

After filters are applied on the left camera's image 
![Filtered](https://github.com/AndreiVladescu/Referential-distance-measurement/blob/main/mask1.png?raw=true)

Measurement taken
![Measurement](https://github.com/AndreiVladescu/Referential-distance-measurement/blob/main/measurement1.png?raw=true)

~~The accuracy is variable; if the camers is close, the error is larger, about 12% of the real distance, and at a longer distance, about 8%.~~
After tests and resolution scaling, I narrowed the accuracy down to 5% (with pre-defined tweaks) at a distance of about 2.5 meters.
