#!/usr/bin/env python

"""
Setup script
"""

import pkg_resources

from setuptools import setup
from noggin.app import __version__


setup(
    name='Noggin',
    description='Noggin Account System',
    version=__version__,
    author='Ryan Lerch
    author_email='rlerch@redhat.com
    maintainer='Ryan Lerch',
    maintainer_email='rlerch@redhat.com',
    license='GPLv2',
    download_url='',
    url='https://pagure.io/noggin',
    packages=['noggin'],
    include_package_data=True,
    install_requires=[
        'Flask', 'python-fedora', 'python-openid', 'python-openid-teams',
        'python-openid-cla'],
)

