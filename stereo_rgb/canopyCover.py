'''
Created on Oct 31, 2016

@author: Zongyang
'''

from PIL import Image, ImageFilter
import numpy as np


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
    """ Generate CSV called fname with fields and trait_list """
    csv = open(fname, 'w')
    csv.write(','.join(map(str, fields)) + '\n')
    csv.write(','.join(map(str, trait_list)) + '\n')
    csv.close()
    return fname


def gen_cc_for_img(img, kernelSize):

    #im = Image.fromarray(img)

    #r, g, b = im.split()

    r = img[:, :, 0]
    g = img[:, :, 1]
    b = img[:, :, 2]

    sub_img = (g.astype('int') - r.astype('int') - 2) > 0

    mask = np.zeros_like(b)

    mask[sub_img] = 255

    im = Image.fromarray(mask)
    blur = im.filter(ImageFilter.BLUR)
    pix = np.array(blur)
    #blur = cv2.blur(mask,(kernelSize,kernelSize))
    sub_mask = pix > 128

    c = np.count_nonzero(sub_mask)
    ratio = c/float(b.size)

    return ratio