from setuptools import find_packages, setup
import os
import sys


setup(
    name='ttc',
    version=0.1.0,
    packages=find_packages(exclude=['tests', 'docs', 'scripts']),
    license='MIT',
    long_description=open('README.rst').read(),
    author='Michael F Bryan',
    description='A scraper for the TTC website',
    install_requires=[
        'pytest',
        'bs4',
        'pytest-cov',
        'requests',
        ],
)
