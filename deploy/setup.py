# encoding: utf8
from setuptools import setup
import os
import sys

long_description = open("README.md").read()
install_requires = [
    'pandoc',
    'jinja2',
    'docopt-ng',
    'ruamel-yaml',
]

setup(
    name="deploy",
    version='0.1.0',
    packages=['deploy'],
    package_data={
        '': [
            'LICENSE'
        ],
    },

    install_requires=install_requires,

    author="Dennis Terhorst",
    author_email="d.terhorst@fz-juelich.de",
    description="Deploy tools based on a YAML config file.",
    long_description=long_description,

    entry_points = {
        'console_scripts': [
            'deploy = deploy.__main__:main',
        ],
    },

    license="GPLv3",

    url='https://github.com/INM-6/Builder',
    # https://pypi.org/pypi?:action=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Public License 3.0 or later',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering']
)
