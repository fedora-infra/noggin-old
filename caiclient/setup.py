#!/usr/bin/env python

"""
Setup script
"""

import os
import pkg_resources
from setuptools import setup


setup(
    name='caiclient',
    description='CAIAPI Client',
    version='0.1',
    author='Ryan Lerch',
    author_email='rlerch@redhat.com',
    maintainer='Ryan Lerch',
    maintainer_email='rlerch@redhat.com',
    license='GPLv2',
    download_url='',
    url='https://pagure.io/noggin',
    packages=['caiclient'],
    include_package_data=True,
    install_requires=['requests'],
    entry_points={
        'console_scripts': [
            'caiclient = caiclient.cli:run',
        ],
    },
)

