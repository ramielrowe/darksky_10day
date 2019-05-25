#!/usr/bin/env python

from setuptools import find_packages, setup, Command

setup(name='darksky_10day',
      version='0.1',
      description='Wunderground 10 Day Emulator for DarkSky',
      author='Andrew Melton',
      author_email='ramielrowe@gmail.com',
      packages=['darksky_10day'],
      include_package_data=True,
      install_requires=[
          'python-dateutil',
          'flask',
          'forecastiopy',
          'redis'
      ]
)
