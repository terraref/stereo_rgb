from setuptools import setup

setup(name='stereo_rgb',
      version='1.0.0',
      packages=['stereo_rgb'],
      include_package_data=True,
      install_requires=[
          'utm', 
          'python-dateutil',
          'influxdb',
      ],
      url='https://github.com/terraref/stereo_rgb',
      )