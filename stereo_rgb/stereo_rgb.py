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
    """Extract height/width information from metadata JSON. Side is left or right."""

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
    """Read image file into array, demosaic, rotate into output image. Optionally save to file."""

    try:
        im = np.fromfile(bin_file, dtype='uint8').reshape(shape[::-1])
        im_color = demosaic(im)
        im_color = (np.rot90(im_color))
        if out_file:
            Image.fromarray(im_color).save(out_file)
        return im_color
    except Exception as ex:
        log.error('Error processing image "%s": %s' % (in_file, str(ex)))
        raise


def demosaic(im):
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
def get_traits_table():
    # Compiled traits table
    fields = ('local_datetime', 'canopy_cover', 'access_level', 'species', 'site',
              'citation_author', 'citation_year', 'citation_title', 'method')
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


def generate_traits_list(traits):
    # compose the summary traits
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


def generate_cc_csv(fname, fields, trait_list):
    """Generate CSV called fname with fields and trait_list."""

    csv = open(fname, 'w')
    csv.write(','.join(map(str, fields)) + '\n')
    csv.write(','.join(map(str, trait_list)) + '\n')
    csv.close()
    return fname


def calculate_canopycover(pxarray):
    """Return greenness percentage of given numpy array of pixels."""

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
