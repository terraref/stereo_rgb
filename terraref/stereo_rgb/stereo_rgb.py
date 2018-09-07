#!/usr/bin/env python

"""stereo_rgb.py: Python functions for interacting with stereo RGB Camera sensor data in TERRA-REF project."""

__author__ = "Joshua Little, Zongyang Li"

import logging
import numpy as np
from scipy.ndimage.filters import convolve
from PIL import Image, ImageFilter

from terrautils.formats import create_geotiff


log = logging.getLogger(__name__)


# bin2tif utilities
def get_image_shape(metadata, side):
    """Extract height/width information from metadata JSON.

    Arguments:
      metadata (dict): cleaned metadata
      side (string): 'right' or 'left'

    Throws:
      RuntimeError: the image format is not 'BayerGR8'
      KeyError: metadata is missing necessary fields
      ValueError: when width and height string can't be cast to int

    Returns:
      (tuple of ints): width and height as tuple
    """

    try:
        im_meta = metadata['sensor_variable_metadata']
        fmt = im_meta['image_format'][side]
        if fmt != 'BayerGR8':
            log.error('Unknown image format %s' % fmt)
            raise RuntimeError('Unknown image format', fmt)
        width = im_meta['width_image_pixels'][side]
        height = im_meta['height_image_pixels'][side]
    except KeyError as err:
        log.error('Metadata file missing key: %s (has it been cleaned using terrautils.metadata.clean_metadata()?)' % err.args[0])
        raise

    try:
        width = int(width)
        height = int(height)
    except ValueError as err:
        log.error('Corrupt image dimension in metadata file')
        raise

    return (width, height)


def process_raw(shape, bin_file, out_file=None):
    """Read image file into array, demosaic, rotate into output image.

    Arguments:
      shape (tuple of ints): the width, height of the bin_file
      bin_file (string): filepath to .bin file to be processed
      out_file (string): filepath where image will be saved (optional)

    Throws:
      various: unable to read .bin file, unable to write image or
               problems with demosaicing

    Returns:
      (numpy array): rotated, demosaiced image
    """

    try:
        im = np.fromfile(bin_file, dtype='uint8').reshape(shape[::-1])
        im_color = demosaic(im)
        im_color = (np.rot90(im_color))
        if out_file:
            Image.fromarray(im_color).save(out_file)
    except Exception as ex:
        log.error('Error creating "%s" from "%s": %s' % \
                  (out_file, bin_file, str(ex)))
        raise

    return im_color


def demosaic(im):
    """Demosaic the BayerGR8 image.

    Arguments:
      im (numpy array): BayerGR8 image with shape (height, width)

    Returns:
      (numpy array): RGB image with shape (height, width)
    """

    # Assuming GBRG ordering.
    B = np.zeros_like(im)
    R = np.zeros_like(im)
    G = np.zeros_like(im)
    R[0::2, 1::2] = im[0::2, 1::2]
    B[1::2, 0::2] = im[1::2, 0::2]
    G[0::2, 0::2] = im[0::2, 0::2]
    G[1::2, 1::2] = im[1::2, 1::2]

    fG = np.asarray(
            [[0, 1, 0],
             [1, 4, 1],
             [0, 1, 0]]) / 4.0
    fRB = np.asarray(
            [[1, 2, 1],
             [2, 4, 2],
             [1, 2, 1]]) / 4.0

    im_color = np.zeros(im.shape+(3,), dtype='uint8') #RGB
    im_color[:, :, 0] = convolve(R, fRB)
    im_color[:, :, 1] = convolve(G, fG)
    im_color[:, :, 2] = convolve(B, fRB)

    return im_color


def bin2tif(inbin, outtif, shape, bounds, metadata):
    """
    :param inbin: a left or right stereoRGB bin file
    :param outtif: output GeoTIFF file
    :param shape: (width, height) of image in pixels derived from sensor_variable_metadata
    :param bounds: bounding box of image derived from spatial_metadata bounding_box
    :param metadata: any metadata to embed inside created geotiff
    """

    img = process_raw(shape, inbin, None)
    create_geotiff(img, bounds, outtif, None, False, extra_metadata=metadata)


# canopycover utilities
def calculate_canopycover(pxarray):
    """Return greenness percentage of given numpy array of pixels.

    Arguments:
      pxarray (numpy array): rgb image

    Returns:
      (float): greenness percentage
    """

    r = pxarray[:, :, 0]
    g = pxarray[:, :, 1]
    b = pxarray[:, :, 2]

    sub_img = (g.astype('int') - r.astype('int') - 2) > 0
    mask = np.zeros_like(b)
    mask[sub_img] = 255

    im = Image.fromarray(mask)
    blur = im.filter(ImageFilter.BLUR)
    blur_pix = np.array(blur)
    sub_mask = blur_pix > 128

    c = np.count_nonzero(sub_mask)
    ratio = c/float(b.size)
    # Scale ratio from 0-1 to 0-100
    ratio *= 100.0

    return ratio

