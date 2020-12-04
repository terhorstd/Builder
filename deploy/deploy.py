#!/usr/bin/env python
# encoding: utf8
'''
Usage: deploy [options] show <config>

Options:
    -v, --verbose       increase output
    -h, --help          print this text
'''
from docopt import docopt
from sys import exit
from functools import total_ordering
from pprint import pformat
from distutils.version import LooseVersion as Version
import logging
log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)
from ruamel.yaml.constructor import DuplicateKeyError
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
        v = self._version
        if self._version is None:
            v = other._version
        return (self._package == other._package and v == other._version and self._variant == other.variant)

    def __lt__(self, other):
        '''
        returns true if package has a lower version than other
        always returns true if self._version is None.

        >>> A = Package("foo")
        >>> B = Package("foo/1.2.3")
        >>> C = Package("bar")
        >>> A < C or C < A
        False
        >>> A < B
        False
        >>> B < A
        False
        '''
        if other._version is None or self._version is None:
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
        >>> B == A
        False
        >>> C = Build("baz")
        >>> A == C
        True
        >>> C == A
        True

        Also having less specific dependencies causes non-parallel builds
        #>>> A = Build("foo/1.2.3")
        #>>> B = Build("bar", ["foo"])
        #>>> A == B
        #False
        #>>> B == A
        #False
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


def red(x):
    return f"\033[31m{x}\033[m"

def green(x):
    return f"\033[32m{x}\033[m"

def blue(x):
    return f"\033[34m{x}\033[m"

def orange(x):
    return f"\033[00;39m{x}\033[m"

def yellow(x):
    return f"\033[00;33m{x}\033[m"

def gray(x):
    return f"\033[00;90m{x}\033[m"

def bold(x):
    return f"\033[01m{x}\033[m"

def CommandsView(deployment):
    output = list()
    done = []
    for build in deployment:
        done_already = []
        output.append(blue(f"\n# Building {build.package}"))
        output.append(gray("module purge"))
        for dep in build.dependencies:
            comment = blue("# ")
            info = gray("system provided")
            if dep in deployment:
                info = green("rebuilt")
            output.append(f"module load {dep:30s}{comment}{info}")
        output.append(bold(f"{build.package.build_command}"))
    return "\n".join(output) + "\n"


class Deployment:
    '''
    Ordered set of Builds

    >>> d = Deployment([
    ...        Build("A", ["B"]),
    ...        Build("B", ["C"]),
    ...        Build("C", ["D"])
    ...     ])
    >>> list(d)
    [C/*/default(), B/*/default(), A/*/default()]

    circular dependencies will raise an error
    >>> d = Deployment([
    ...        Build("A", ["B"]),
    ...        Build("B", ["C"]),
    ...        Build("C", ["A"])
    ...     ])
    >>> list(d)
    Traceback (most recent call last):
       ...
    ValueError: package A/*/default seems to have a cyclic dependency!
    '''
    def __init__(self, builds=[]):
        self._builds = builds

    def show(self):
        print(CommandsView(self))

    def append(self, build):
        assert isinstance(build, Build), "Deployments can only hold Build objects, not %s" % type(build)
        self._builds.append(build)

    def __iter__(self):
        '''
        odered iterator
        raises ValueError if packages are not oderable


        '''
        done = []
        for build in sorted(self._builds):
            if any([build.package in donepkg.dependencies for donepkg in done]):
                raise ValueError("package %s seems to have a cyclic dependency!" % build.package)
            yield build
            done.append(build)

    def __contains__(self, package):
        '''
        >>> A = Build("foo")
        >>> B = Build("bar", ["foo", "baz"])
        >>> D = Deployment([A,B])
        >>> A.package in D
        True
        >>> B.package in D
        True
        >>> print(D._builds)
        [foo/*/default(), bar/*/default()]
        >>> Package("baz") in D
        False
        '''
        return package in [depl.package for depl in self._builds]


def read_config(filename):
    yaml.allow_duplicate_keys = False
    try:
        with open(filename, 'rb') as infile:
            return yaml.load(infile)
    except DuplicateKeyError as e:
        log.error("%s", e)
        exit(2)


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
