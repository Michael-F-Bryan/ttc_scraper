from setuptools import find_packages, setup
import os
import sys


setup(
    name='ttc_scraper',
    version='0.1.0',
    packages=find_packages(exclude=['tests', 'docs', 'scripts']),
    license='MIT',
    long_description=open('README.rst').read(),
    author='Michael F Bryan',
    entry_points = {
        'console_scripts': ['scrape_ttc=ttc_scraper.__main__:main'],
    },
    description='A scraper for the TTC website',
    install_requires=[
        'bs4',
        'requests',
        ],
)
