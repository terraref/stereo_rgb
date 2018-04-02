# stereo_rgb science package

This repository contains utilities for scientific operations on Stereo RGB camera data.

### stereo_rgb.py

**get_image_shape(metadata, side)**
Parse LemnaTec metadata JSON for a particular side (left/right) to get image dimensions.

**process_raw(shape, bin_file, out_file=None)**
Convert a raw BIN file to a georeferenced GeoTIFF.

**calculate_canopycover(pxarray)**
Calculate the percentage of given pixel array over greenness threshold to be considered canopy.

### Authors:

* Zongyang Li, Donald Danforth Plant Science Center, St. Louis, MO
* Maxwell Burnette, National Supercomputing Applications, Urbana, Il
* Robert Pless, George Washington University, Washington, DC
