#!/usr/bin/env python

"""
Setup script
"""

import os
import pkg_resources
from setuptools import setup


with open(os.path.join(os.path.dirname(__file__), '../VERSION'), 'r') as v:
    VERSION = v.read().strip()


setup(
    name='CAIAPI',
    description='Community Account Information Application Programming Interface',
    version=VERSION,
    author='Ryan Lerch',
    author_email='rlerch@redhat.com',
    maintainer='Ryan Lerch',
    maintainer_email='rlerch@redhat.com',
    license='GPLv2',
    download_url='',
    url='https://pagure.io/noggin',
    packages=['CAIAPI'],
    include_package_data=True,
    install_requires=['Flask'],
)

