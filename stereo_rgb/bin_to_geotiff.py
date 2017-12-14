#!/usr/bin/env python

'''
Created on May 3, 2016
Author: Joshua Little, Zongyang Li
'''

import sys, os.path, json
import numpy as np
from scipy.ndimage.filters import convolve
from PIL import Image


def get_image_shape(metadata, which):
    try:
        im_meta = metadata['sensor_variable_metadata']
        fmt = im_meta['image_format'][which]
        if fmt != 'BayerGR8':
            fail('Unknown image format: ' + fmt)
        width = im_meta['width_image_pixels'][which]
        height = im_meta['height_image_pixels'][which]
    except KeyError as err:
        fail('Metadata file missing key: ' + err.args[0])

    try:
        width = int(width)
        height = int(height)
    except ValueError as err:
        fail('Corrupt image dimension, ' + err.args[0])
    return (width, height)

def process_image(shape, in_file, out_file=None):

    try:
        im = np.fromfile(in_file, dtype='uint8').reshape(shape[::-1])
        im_color = demosaic(im)
        im_color = (np.rot90(im_color))
        if out_file:
            Image.fromarray(im_color).save(out_file)
        return im_color
    except Exception as ex:
        fail('Error processing image "%s": %s' % (in_file, str(ex)))

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

def fail(reason):
    print >> sys.stderr, reason
