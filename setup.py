from setuptools import setup

setup(name='stereo_rgb',
      version='1.0.0',
      packages=['stereo_rgb'],
      include_package_data=True,
      url='https://github.com/terraref/stereo_rgb',
      entry_points={
          'console_scripts': [
              'stereo_match = stereo_rgb.stereo_match:main'
          ]
      },
      )
