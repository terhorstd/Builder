#!/usr/bin/env python
# encoding: utf8
'''
Usage: deploy [options] show <config>

Options:
    -v, --verbose       increase output
    -h, --help          print this text
'''
from docopt import docopt

from functools import total_ordering
from pprint import pformat
from distutils.version import LooseVersion as Version
import logging
log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)
from ruamel.yaml import YAML
yaml = YAML()

class Package:
    def __init__(self, package, version=None, variant="default"):
        '''
        >>> Package("A")
        A/*/default
        >>> Package("B", "0.1")
        B/0.1/default
        >>> Package("c", "0.2", "testing")
        c/0.2/testing
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
            pvv = package.split('/',3)
            if pvv:
                self._package = pvv.pop(0)
            if pvv:
                self._version = pvv.pop(0)
            if pvv:
                self._variant = pvv.pop(0)

    @property
    def name(self):
        return self._package

    @property
    def version(self):
        return self._version

    @property
    def variant(self):
        return self._variant

    def __eq__(self, other):
        return (self._package == other._package and self._version == other._version and self._variant == other.variant)

    def __lt__(self, other):
        '''
        returns true if package has a lower version than other
        always returns true if self._version is None.
        '''
        if other._version is None:
            return False
        return self._version is None or self._version < other._version

    def __format__(self, fmt):
        v = self._version or "*"
        text = f'{self._package}/{v}/{self._variant}'
        return ('{:'+fmt+'}').format(text)

    def __repr__(self):
        v = self._version or "*"
        return f'{self._package}/{v}/{self._variant}'

    @property
    def build_command(self):
        if self._version is None:
            return f"build {self._package}"
        if self._variant != "default":
            return f"build {self._package} {self._version} {self._variant}"
        return f"build {self._package} {self._version}"



@total_ordering
class Build:
    def __init__(self, package, dependencies=[]):
        self._package = Package(package)
        self._dependencies = [Package(dep) for dep in dependencies]

    @property
    def package(self):
        return self._package

    @property
    def dependencies(self):
        yield from self._dependencies

    def __eq__(self, other):
        '''
        returns true if two packages can be built at the same time
        i.e. no dependencies between the two packages
        >>> A = Build("foo")
        >>> B = Build("bar", ["foo"])
        >>> A == B
        False
        >>> C = Build("baz")
        >>> A == C
        True
        '''
        return (self._package == other._package
                or
                ( self._package not in other._dependencies
                  and other._package not in self._dependencies))

    def __repr__(self):
        return f'{self._package}()'

    def __lt__(self, other):
        '''
        returns true if this build has to run before the other

        >>> A = Build("foo")
        >>> B = Build("bar", ["foo"])
        >>> A < B
        True
        >>> B < A
        False
        >>> C = Build("baz")
        >>> A < C
        False
        '''
        return self._package in other._dependencies or any([self._package < dep for dep in other._dependencies])


def CommandsView(deployment):
    output = list()
    done = []
    for build in deployment:
        done_already = []
        output.append(f"\033[01;33m# Building {build.package}\033[m")
        output.append("module purge")
        for dep in build.dependencies:
            info = build in deployment
            output.append(f"module load {dep:30s}{info}")
        output.append(f"build {build.package.build_command}")
    return "\n".join(output) + "\n"


class Deployment:
    def __init__(self, builds=[]):
        self._builds = builds

    def show(self):
        print(CommandsView(self))

    def append(self, build):
        assert isinstance(build, Build), "Deployments can only hold Build objects, not %s" % type(build)
        self._builds.append(build)

    def __iter__(self):
        yield from sorted(self._builds)

    def __contains__(self, build):
        '''
        >>> A = Build("foo")
        >>> B = Build("bar", ["foo", "baz"])
        >>> D = Deployment([A,B])
        >>> A in D
        True
        >>> B in D
        True
        >>> print(D._builds)
        >>> Build("buz") in D
        False
        '''
        for b in self._builds:
            cmp_is = build is b
            cmp_eq = build == b
            print(f"{build} is {b}? {cmp_is} {cmp_eq}")
        return build in self._builds


def read_config(filename):
    with open(filename, 'rb') as infile:
        return yaml.load(infile)


def main():
    args = docopt(__doc__)
    if args['--verbose']:
        log.setLevel(logging.DEBUG)
    log.debug(pformat(args))

    log.info("Hello World")

    config = read_config(args['<config>'])
    plan = Deployment()
    for package, dependencies in config.items():
        plan.append(Build(package, dependencies))

    if args['show']:
        plan.show()


if __name__ == '__main__':
    main()
