#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="solidity-parser",
    version="0.0.1",
    packages=["solidity_parser"],
    author="tintinweb",
    author_email="tintinweb@oststrom.com",
    description=(
        "A Solidity parser for Python built on top of a robust ANTLR4 grammar"),
    license="MIT",
    keywords=["solidity","parser","antlr"],
    url="https://github.com/consensys/python-solidity-parser/",
    download_url="https://github.com/consensys/python-solidity-parser/tarball/v0.0.1",
    #python setup.py register -r https://testpypi.python.org/pypi
    #long_description=read("README.rst") if os.path.isfile("README.rst") else read("README.md"),
    install_requires=["antlr4-python3-runtime"],
    #test_suite="nose.collector",
    #tests_require=["nose"],
)