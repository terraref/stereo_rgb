import os
import json
import tempfile
import shutil
import sys
import subprocess

lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)

from stereo_rgb import stereo_rgb
from terrautils.metadata import clean_metadata, get_terraref_metadata
from terrautils.formats import create_geotiff
from terrautils.spatial import geojson_to_tuples


test_id = 'aa2ffdb2-4b44-4828-ae3c-9be5698241ca'
path = os.path.join(os.path.dirname(__file__), 'test_stereo_rgb_doc', test_id)
dire = os.path.join(os.path.dirname(__file__), 'test_stereo_rgb_doc')
pa_dire = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stereo_rgb')

# TODO: Automatically download these files from Clowder Sample Data collection if they don't exist
meta_file = path + '_metadata.json'
img_left = path + '_left.bin'
out_tmp_tiff = os.path.join(tempfile.gettempdir(), test_id.encode('utf8'))

# Clean raw metadata file
with open(path + '_metadata.json', 'rb') as f:
    raw_metadata = json.load(f)
cleanmetadata = clean_metadata(raw_metadata, "stereoTop")
metadata = get_terraref_metadata(cleanmetadata, 'stereoTop')


# TODO: This should go in terrautils testing, not here
def test_clean_data():
    assert 'sensor_variable_metadata' in cleanmetadata.keys()

# TODO: This should go in terrautils testing, not here
def test_terra_subset():
    assert 'terraref_cleaned_metadata' in metadata.keys()


# Perform actual conversions
left_shape = stereo_rgb.get_image_shape(metadata, 'left')
left_image = stereo_rgb.process_raw(left_shape, img_left, None)
left_gps_bounds = geojson_to_tuples(metadata['spatial_metadata']['left']['bounding_box'])
create_geotiff(left_image, left_gps_bounds, out_tmp_tiff, None, False, None, metadata)
shutil.move(out_tmp_tiff, path + '_test_result.tif')


def test_stereo_rgb():
    assert left_shape == (3296, 2472)

def test_output_file():
    assert os.path.isfile(path + '_test_result.tif')
    

if __name__ == '__main__':
    subprocess.call(['python -m pytest test_stereo_rgb.py -p no:cacheprovider'], shell=True)


