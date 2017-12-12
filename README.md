# Stereo 3D RGB extractors

This repository contains extractors that process data originating from the GT3300C 8MP RGB Camera.

## Bin2Tif Extractor

Stereo RGB Image Bin to GeoTIFF Converter.

### Authors:

* Zongyang Li, Donald Danforth Plant Science Center, St. Louis, MO
* Maxwell Burnette, National Supercomputing Applications, Urbana, Il
* Robert Pless, George Washington University, Washington, DC

### Overview

This extractor processes binary stereo images using metadata and outputs JPG and TIFF images.

The extractor execution is triggered when required input files are added to a dataset.

_Input_

- Following data must be found
  - _left.bin image
  - _right.bin image
  - dataset metadata for the left+right capture dataset; can be attached as Clowder metadata or included as a metadata.json file

_Output_

- The dataset containing the left/right binary images will get left/right JPG and geoTIFF images.
- Metadata, including geospatial information will be added to the geoTIFF file as well as to the geostreams database.

### Algorithm

#### Algorithm Description

1. Convert raw data to 3 channels color image

   Stereo RGB camera uses a single charge-coupled device (CCD) sensor, with the CCD pixels preceded in the optical path by a color filter array(CFA) in a Bayer mosaic pattern.
   For each 2x2 set of pixels, two diagonally opposed pixels have green filters, and the other two have red and blue filters.
   We assume  these pixels are in a GBRG ordering, and use bilinear interpolation to do the demosaicing.
   This means that three color planes are independently interpolated using symmetric bilinear interpolation from the nearest neighbors of the same color.

**Reference: Malvar, H.S., L. He, and R. Cutler, High quality linear interpolation for demosaicing of Bayer-patterned color images. ICASPP, Volume 34, Issue 11, pp. 2274-2282, May 2004.**

2. Steps for geo-referencing bounding box to each image.

    a. Get image shape from metadata,

    b. Get camera center position from metadata

    c. Compute field of view for the image:

        i. The JSON data reports the camera field of view as "the field of view for a scene 2 meters away is: “0.749m x 1.015m"

        ii. Predict fov for each image should be:

            * fix_fov = fov_in_2_meter*(camera_height/2)

        iii. In implementing the stitching process, we required two magic numbers that are computed experimentally to get the correct geometric alignment.  Our experimentally determined values are:

             * HEIGHT_MAGIC_NUMBER = 1.64

             * PREDICT_MAGIC_SLOPE = 0.574

        iv. These numbers are used in the following equations.

		      * predict_plant_height = PREDICT_MAGIC_SLOPE * camHeight

	  	    * camH_fix = camHeight + HEIGHT_MAGIC_NUMBER - predict_plant_height

		      * fix_fov_x = fov_x*(camH_fix/2)

		      * fix_fov_y = fov_y*(camH_fix/2)

    e. Steps for computing the Magic Numbers:

        i. Make an assumption that the real FOV can be derived as a linear function base on the given FOV.
        ii. Randomly pick several different days stereoTop RGB raw data in different camera height, try to get a best stitched full field map for each day empirically(by personal judgement), and record all the FOV for each day.
        iii. Apply a linear regression to output HEIGHT_MAGIC_NUMBER and PREDICT_MAGIC_SLOPE

     d. Compute geo-reference bounding box

          i. Convert coordinates from Scanalyzer to MAC coordinates using formula from [https://terraref.gitbooks.io/terraref-documentation/content/user/geospatial-information.html](https://terraref.gitbooks.io/terraref-documentation/content/user/geospatial-information.html)

         ii. Use utm tools to convert coordinates from MAC to lat/lon
     e. Using [osgeo.gdal](http://www.osgeo.org/gdal_ogr), associate image with geospatial bounding box, and create geoTIFF.

#### Parameters

HEIGHT_MAGIC_NUMBER and PREDICT_MAGIC_SLOPE were applied when we estimate the field of view, these are empirically derived values as described in the above algorithm.

The geo-reference bounding box is based on the assumption that image is aligned to geographic coordinates, so that moving up in the image corresponds to moving exactly north.
 We expect that error in the relative location of pixels within an image introduced by this assumption is much less than the pixel resolution.

#### Limitations

1. Any stitched image introduces new artifacts into the image data; it always introduces edges at the boundary of where one image turns into another --- either an explicitly black line boundary or an implicit boundary that is there because you can't exactly stitch images of a complicated 3D world (without making a full 3D model). Even if you could stitch them, the same bit of the world is usually a different brightness when viewed from different directions.
2. The stitched full field image may have artifacts that arise from harsh shadows in some imaging conditions.
3. One of the artifacts is duplication of area, this is unavoidable without a much more complex stitching algorithm that implicitly infers the 3D structure of the ground. The justification for not going for such a rich representation is that:
  1. for the plants, since they move, it would be impossible not to have artifacts at the edges of the image, and
  2. for the ground, we judged that small stitching errors were not worth the (substantial) additional effort to build the more complete model.

#### Failure Conditions

* If the camera is moved in the gantry box, then the magic numbers may have to be recalculated or experimentally determined.

* If the camera is not aligned north-south, then the geo-bounding box may not be accurate.


### Application

#### Files

* Dockerfile: defines docker image with all dependencies
* batch_launcher.sh: used to submit jobs on ROGER cluster
* bin_to_geotiff.py:
* terra_bin2tif.py: extractor (wrapper for bin_to_geotiff.py)
* entrypoint.sh, extractor_info.json, terra.bin2tif.service: Clowder utilities

#### Docker

The Dockerfile included in this directory can be used to launch this extractor in a docker container.

_Building the Docker image_

```sh
docker build -f Dockerfile -t terra-ext-bin2tif .
```

_Running the image locally_

```sh
docker run \
  -p 5672 -p 9000 --add-host="localhost:{LOCAL_IP}" \
  -e RABBITMQ_URI=amqp://{RMQ_USER}:{RMQ_PASSWORD}@localhost:5672/%2f \
  -e RABBITMQ_EXCHANGE=clowder \
  -e REGISTRATION_ENDPOINTS=http://localhost:9000/clowder/api/extractors?key={SECRET_KEY} \
  terra-ext-bin2tif
```

_Note_: by default RabbitMQ will not allow "guest:guest" access to non-local addresses, which includes Docker. You may need to create an additional local RabbitMQ user for testing.

_Running the image remotely_

```sh
docker run \
  -e RABBITMQ_URI=amqp://{RMQ_USER}:{RMQ_PASSWORD}@rabbitmq.ncsa.illinois.edu/clowder \
  -e RABBITMQ_EXCHANGE=terra \
  -e REGISTRATION_ENDPOINTS=http://terraref.ncsa.illinosi.edu/clowder//api/extractors?key={SECRET_KEY} \
  terra-ext-bin2tif
```

#### Cluster Computing with TORQUE/PBS

The extractor can also be run on a compute cluster via the TORQUE/PBS batch system. These instructions are for use on [ROGER](https://wiki.ncsa.illinois.edu/display/ROGER/ROGER%3A+The+CyberGIS+Supercomputer).

This process assumes that you are using the existing Python virtualenv under:

```
/projects/arpae/terraref/shared/extractors/pyenv/
```

This also uses a shared environment file for common settings:

```
/projects/arpae/terraref/shared/extractors/env.sh
```

The following default batch jobs will start 20 extractors on a single 20-core node:

```
qsub /projects/arpae/terraref/shared/extractors/extractors-stereo-rgb/bin2tif/batch_launcher.sh
```

#### Dependencies

* All of the Python scripts syntactically support Python >= 2.7. Please make sure that the Python in the running environment is in appropriate version.

* All the Python scripts also rely on the third-party library including: PIL, scipy, numpy and osgeo.



## Canopy cover extractor
This extractor processes binary stereo images and generates values of plot-level percent canopy cover traits that are inserted into the BETYdb trait database.

 The core idea for this extractor is a plant-soil segmentation.
 We apply a threshold to differentiate plant and soil, and do a smoothing after binary processing.
 From this difference, it returns a plant area ratio within the bounding box.

_Input_

  - Evaluation is triggered whenever a file is added to a dataset
  - Following data must be found
    - _left.bin image
    - _right.bin image
    - dataset metadata for the left+right capture dataset; can be attached as Clowder metadata or included as a metadata.json file

_Output_

  - The configured BETYdb instance will have canopy coverage traits inserted

## Height recovery

## Stereo texture analysis
### GIFT - a tool to extract green index based features

This tool extracts color and texture features from an RGB image.
The color image is converted into a dark green color indexed (DGCI) image
and the distribution of indexed value computed as intensity histogram.
Texture analysis is done by finding edges within the DGCI image and then
counting the edge pixels.


This is a bash shell script that was tested on

    No LSB modules are available.
    Distributor ID: Ubuntu
    Description:    Ubuntu 12.04.5 LTS
    Release:        12.04
    Codename:       precise



### Getting Started

use gift.sh to process a single .raw image file.

For example


    ./gift.sh  SamplePlant_Whitetarget/stereoTop/2016-04-30__08-57-55-804/8b924dc8-0500-4dc1-846b-b82bebb9c94f_left.bin

To process a batch of images try the following command

    find . -name "*.bin" | xargs -i ./gift.sh {}


The .bin file (raw image) is converted into a color image using two helper tools (cf prerequisites).
Then the output tmp.png is pass over to gift.R script.
The extraction of image features is done via R, and the output can be modified using the command line options.
Try this

    Rscript gift.R -h



### Output

There four different output available with gift.R, each can be enable|disabled;  per default no output is
returned!

-table.csv
  This file contains the feature vectors per image or region of interest. Following fields are available:

  - roi = label of region of interest [1..N]
  - area = area of count of pixelsROI
  - edges =
  - dgci.-0.1 .. dgci.2.9 = histogram bins ranging from DGCI values -.1 to 2.9;  the values represent
    frequency counts
  - m.cx = center of mass x coordinate
  - m.cy = center of mass y coordinate
  - m.majoraxis =
  - m.eccentricity = eccentricity of shape
  - m.theta =
  - s.area = area of region of interest
  - s.perimeter = perimeter of shape
  - s.radius.mean = mean radius of shape
  - s.radius.sd = standard deviation of mean radius
  - s.radius.min = minimal radius
  - s.radius.max = maximal radius


-dgci.png
  This is the dark green color indexed image of the original color image.

-edge.png
  On the basis of the DGCI-image, sharp edges are detected and represented as white pixels in the output
  b/w image.

-label.png
  If an image mask with region of interest (ROI) was used, then this output represent the labeled ROIs.


#### Prerequisites

Several tools are necessary to run this script:-

- bayer2rgb [https://github.com/jdthomas/bayer2rgb]
- imagemagick [https://www.imagemagick.org/script/index.php]
- R [https://cran.r-project.org/]
  - R libraries:-
    - EBImage [https://bioconductor.org/packages/release/bioc/html/EBImage.html]
    - dplyr [https://cran.r-project.org/web/packages/dplyr/index.html]
    - optparse [https://cran.r-project.org/web/packages/optparse/index.html]


#### Installing

Depending on your linux distribution use the repository to install the packages.
For example on ubuntu do

```sh
sudo apt-get install imagemagick r-base r-baes-core
```

For all the R libraries use the following:

```r
install.packages("devtools", dependent=T)
install.packages("optparse", dependent=T)

## Install EBImage following instructions https://bioconductor.org/packages/release/bioc/html/EBImage.html
source("https://bioconductor.org/biocLite.R")
biocLite("EBImage")
```

#### Running the tests

check that bayer2rgb works

```sh
bayer2rgb  -t -i gift-test.bin"$@" -o gift-test.tif -v  2472 -w 3296 -b 8 -m AHD -f GRBG
```


check that tif to png works with imagemagick's convert tool

```sh
convert gift-test.tif gift-test.png  ### some warning messages may pop up
```

check that gift.R works

```sh
Rscript gift.R -h

Rscript gift.R -f gift-test.png -t ### should return a tmp-table.csv file

Rscript gift.R -f gift-test.png -t -d -e -l ### should return all output files

Rscript gift.R -f gift-test.png -t -r roi.png ### this analysis the image using a b/w image as ROI mask
```

finally check that gift.sh works

```sh
./gift.sh  gift-test.tiff
```

### Authors

Kevin Nagel / kevin.nagel@lemnatec.com

2017-03-23