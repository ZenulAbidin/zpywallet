#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open
from os import path
import re

# Get the long description from the README file
with open(path.join('README.rst'), encoding='utf-8') as f:
    long_description = f.read()

def load_version():
    version_file = "zpywallet/_version.py"
    version_line = open(version_file).read().rstrip()
    vre = re.compile(r'__version__ = "([^"]+)"')
    matches = vre.findall(version_line)

    if matches and len(matches) > 0:
        return matches[0]
    else:
        raise RuntimeError(
            "Cannot find version string in {version_file}.".format(
                version_file=version_file))

version = load_version()

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name='zpywallet',
    version=version,
    description="Multi-coin BIP32 (HD) wallet creation, transaction listener, creation and broadcasting",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/ZenulAbidin/pywallet',
    author='Ali Sherief',
    author_email='ali@notatether.com',
    license='MIT',
    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",
        "Operating System :: OS Independent",

        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    platforms = ['any'],
    keywords='bitcoin, wallet, litecoin, hd-wallet, dogecoin, dashcoin, ethereum, address, crypto, python',
    packages = find_packages(exclude=['contrib', 'docs', 'tests', 'demo', 'demos', 'examples']),
    include_package_data=True,
    exclude_package_data={"": ["__pycache__/*", "*.py[cod]"]},
    install_requires=install_requires,
    python_requires=">=3.10"
)
