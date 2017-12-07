from setuptools import setup

setup(name='bin2geotiff',
      version='1.0.0',
      packages=['bin2geotiff'],
      include_package_data=True,
      install_requires=[
          'utm', 
          'python-dateutil',
          'influxdb',
      ],
      url='https://github.com/terraref/bin2geotiff',
      )