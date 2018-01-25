#!/usr/bin/env python

"""stereo_rgb.py: Python functions for interacting with stereo RGB Camera sensor data in TERRA-REF project."""

__author__ = "Joshua Little, Zongyang Li"


import numpy as np
from scipy.ndimage.filters import convolve
from PIL import Image, ImageFilter

import logging
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
        log.error('Metadata file missing key: %s' % err.args[0])
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


# canopycover utilities

# TODO if the order of the fields is important use an ordered dict
def get_traits_table():
    """Return trait dictionary and field array.

    Returns:
      (tuple): tuple with field tuple and traits dictionary
    """

    # Compiled traits table
    fields = ('local_datetime', 'canopy_cover', 'access_level', 'species',
              'site', 'citation_author', 'citation_year', 'citation_title',
              'method')
    traits = {'local_datetime': '',
              'canopy_cover': [],
              'access_level': '2',
              'species': 'Sorghum bicolor',
              'site': [],
              'citation_author': '"Zongyang, Li"',
              'citation_year': '2016',
              'citation_title': 'Maricopa Field Station Data and Metadata',
              'method': 'Canopy Cover Estimation from RGB images'}

    return (fields, traits)


# TODO use ordereddict
def generate_traits_list(traits):
    """Return trait data as a list in known order.

    Arguments:
      traits (dict): trait data with well known fields

    Returns:
      (list): 
    """

    trait_list = [traits['local_datetime'],
                  traits['canopy_cover'],
                  traits['access_level'],
                  traits['species'],
                  traits['site'],
                  traits['citation_author'],
                  traits['citation_year'],
                  traits['citation_title'],
                  traits['method']
                  ]

    return trait_list


def generate_cc_csv(fname, fields, traits):
    """Generate CSV called fname with fields and trait_list.

    Arguments:
      fname (string): filepath where CSV will be written
      fields (list): column labels
      traits (list): column values

    Throws:
      IOError: unable to write CSV file (file permissions?)
      RuntimeError: fields and traits list are not the same length

    Returns:
      (string): the path to the CSV (same as input parameter)
    """ 

    if len(fields) != len(traits):
        log.debug('fields = %s, traits = %s', fields, traits)
        raise RuntimeError('fields and traits lists are not same length')

    try:
        csv = open(fname, 'w')
        csv.write(','.join(map(str, fields)) + '\n')
        csv.write(','.join(map(str, traits)) + '\n')
        csv.close()
    except IOError as ex:
        log.error('unable to write CSV file: {}'.format(fname))
        raise

    return fname


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

    return ratio

