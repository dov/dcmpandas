#!/usr/bin/env python

from distutils.core import setup

setup(name='dcmpandas',
      version='0.01',
      description='scraper and utility functions for reading a dicom files with pandas',
      author='Dov Grobgeld',
      author_email='dov.grobgeld@gmail.com',
      url='https://github.com/dov/dcmpandas',
      py_modules=['dcmpandas'],
      requires = ['dicom']
      )

