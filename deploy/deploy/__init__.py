#!/usr/bin/env python
# encoding: utf8
#
#   __init__.py – part of the "deploy" build automation system
#   Copyright (C) 2020  Dennis Terhorst
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
'''
Deploy main module.

This module holds the main data object definitions "Package", "Build" and
"Deployment". Additionally, currently there is the config loader for yaml
files.
'''
import sys
import logging

from distutils.version import LooseVersion as Version
from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError
yaml = YAML()

log = logging.getLogger(__name__)


class Package:
    '''
    Representation of a single software package.

    Packages have a name, version and variant, where version and variant
    default to None and "default" respectively.

    >>> Package("A")
    A/*/default

    Packages support pythonic operations:

    >>> l = [Package("foo")]
    >>> Package("foo/1.2") in l
    False
    >>> l = [Package("foo")]
    >>> Package("foo") in l
    True
    '''

    def __init__(self, package, version=None, variant="default"):
        '''
        Create package instance.

        Initialize the Package instance either from explicitly separate values
        or from a combined package string.

        Explicitly:
        >>> Package("A")
        A/*/default
        >>> Package("B", "0.1")
        B/0.1/default
        >>> Package("c", "0.2", "testing")
        c/0.2/testing

        By package strings:
        >>> Package("d/0.3.1")
        d/0.3.1/default
        >>> Package("d/0.4/foo")
        d/0.4/foo
        '''
        if isinstance(package, Package):
            variant = package.variant
            version = package.version
            package = package.package

        if isinstance(version, str):
            version = Version(version)

        self._package = package
        self._version = version
        self._variant = variant
        if "/" in package:
            if version is not None:
                raise ValueError("can not have version in package and version arugments")
            pvv = package.split('/', 3)
            if pvv:
                self._package = pvv.pop(0)
            if pvv:
                self._version = pvv.pop(0)
            if pvv:
                self._variant = pvv.pop(0)

    @property
    def name(self):
        '''
        Plain package name, without version or variant.

        Returns
        -------
        str:  plain package name
        '''
        return self._package

    @property
    def version(self):
        '''
        Version-specifier of this Package.

        Returns
        -------
        str, None:  version specifier of the package
        '''
        return self._version

    @property
    def variant(self):
        '''
        Version-specifier of this Package.

        Returns
        -------
        str:  variant of the package
        '''
        return self._variant

    def __eq__(self, other):
        '''
        Test for equality.

        A Package is considered equal to another package, if the triplet (name,
        version, variant) is equal.
        '''
        return (self._package == other._package
                and self._version == other._version
                and self._variant == other.variant)

    def __lt__(self, other):
        '''
        Test for version order.

        Returns true if package has a lower version than other
        always returns true if self._version is None.

        >>> A = Package("foo")
        >>> B = Package("foo/1.2.3")
        >>> C = Package("bar")
        >>> A < C or C < A
        Traceback (most recent call last):
          ...
        ValueError: No version order between different packages!
        >>> A < B
        False
        >>> B < A
        False
        '''
        if self._package != other._package:
            raise ValueError("No version order between different packages!")
        if other._version is None or self._version is None:
            return False
        return self._version is None or self._version < other._version

    def __format__(self, fmt):
        'Apply standard string formatting (s) to name/version/variant string.'
        ver = self._version or "*"
        text = f'{self._package}/{ver}/{self._variant}'
        return ('{:'+fmt+'}').format(text)

    def __repr__(self):
        'Return Package representation.'
        ver = self._version or "*"
        return f'{self._package}/{ver}/{self._variant}'

    @property
    def load_command(self):
        '''
        Shell commands to preload this package.

        Returns
        -------
        str : shell commands to preload this package to be used by a build
        '''
        if self._version is None:
            return f"module load {self._package}"
        if self._variant != "default":
            return f"module load {self._package}/{self._version}/{self._variant}"
        return f"module load {self._package}/{self._version}"

    @property
    def build_command(self):
        '''
        Shell command to build this package.

        Returns
        -------
        str : shell command to build this package (not including any module loads)
        '''
        if self._version is None:
            return f"build {self._package}"
        if self._variant != "default":
            return f"build {self._package} {self._version} {self._variant}"
        return f"build {self._package} {self._version}"


class Build:
    'A single build in a deployment.'

    def __init__(self, package, dependencies=None):
        if dependencies is None:
            dependencies = []
        self._package = Package(package)
        self._dependencies = [Package(dep) for dep in dependencies]

    @property
    def package(self):
        'Return main Package to be built.'
        return self._package

    @property
    def dependencies(self):
        'Yield all packages this build depends on.'
        yield from self._dependencies

    def __repr__(self):
        'Return Build representation.'
        return f'{self._package}(%s)' % "; ".join([str(d) for d in self._dependencies])


class Deployment:
    '''
    Ordered set of Builds.

    >>> d = Deployment([
    ...        Build("A", ["B"]),
    ...        Build("B", ["C"]),
    ...        Build("C", ["D"])
    ...     ])
    '''

    def __init__(self, builds=None):
        if builds is None:
            builds = []
        self._builds = builds

    def append(self, build):
        '''
        Add a given build to the deployment.

        Order may be irrelevant.
        '''
        assert isinstance(build, Build), "Deployments can only hold Build objects, not %s" % type(build)
        self._builds.append(build)

    def __contains__(self, package):
        '''
        Check if the deployment already contains a given build.

        >>> A = Build("foo")
        >>> B = Build("bar", ["foo", "baz"])
        >>> D = Deployment([A,B])
        >>> A.package in D
        True
        >>> B.package in D
        True
        >>> print(D._builds)
        [foo/*/default(), bar/*/default(foo/*/default; baz/*/default)]
        >>> Package("baz") in D
        False
        '''
        return package in [depl.package for depl in self._builds]


def read_config(filename):
    '''
    Read a yaml config file.

    Parameters
    ----------
    filename : str, Path
        config file

    Returns
    -------
    data object : the data as read from the YAML file.
    '''
    yaml.allow_duplicate_keys = False
    try:
        with open(filename, 'rb') as infile:
            return yaml.load(infile)
    except DuplicateKeyError as err:
        log.error("%s", err)
        sys.exit(2)
