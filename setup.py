#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

deps (requires up2date version):
    *) pip install --upgrade pip wheel setuptools twine
publish to pypi w/o having to convert Readme.md to RST:
    1) #> python setup.py sdist bdist_wheel
    2) #> twine upload dist/*   #<specify bdist_wheel version to upload>; #optional --repository <testpypi> or  --repository-url <testpypi-url>

'''
import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


version = "0.0.7"
name = "solidity-parser"

setup(
    name=name,
    version=version,
    packages=find_packages(),
    author="tintinweb",
    author_email="tintinweb@oststrom.com",
    description=(
        "A Solidity parser for Python built on top of a robust ANTLR4 grammar"),
    license="MIT",
    keywords=["solidity","parser","antlr"],
    url="https://github.com/consensys/python-%s/"%name,
    download_url="https://github.com/consensys/python-%s/tarball/v%s"%(name, version),
    long_description=read("README.md") if os.path.isfile("README.md") else "",
    long_description_content_type='text/markdown',
    #python setup.py register -r https://testpypi.python.org/pypi
    install_requires=["antlr4-python3-runtime"],
    #test_suite="nose.collector",
    #tests_require=["nose"],
)
