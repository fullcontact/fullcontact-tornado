#!/usr/bin/python

from setuptools import setup, find_packages

from version import get_version

readme = open('README.md').read()

install_requires = [
    'tornado>=4.3',
]

setup(
    name="fullcontact-tornado",
    version=get_version('short'),
    author="Kaspars Dancis",
    author_email="kaspars@fullcontact.com",
    description="A Cab api client",
    long_description=readme,
    platforms=[ 'any' ],
    license="Eclipse Public License",
    url="https://github.com/fullcontact/fullcontact-tornado",
    packages=["fullcontact"],
    install_requires=install_requires,
)
