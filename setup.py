from setuptools import find_packages, setup

setup(name='terraref-stereo_rgb',
      version='1.0.3',
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
