from setuptools import find_packages, setup

def description():
      with open('readme.rst') as f:
            return f.read()

setup(name='terraref-stereo_rgb',
      version='1.0.4',
      description='TERRA-REF stereo RGB camera science package',
      long_description=description(),
      packages=find_packages(),
      namespace_packages=['terraref'],
      include_package_data=True,
      url='https://github.com/terraref/stereo_rgb',
      install_requires=[
            'numpy',
            'scipy',
            'multiprocessing',
            'matplotlib',
            'Pillow'
      ]
      )
