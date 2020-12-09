#!/usr/bin/env python
# encoding: utf8
'''
Usage: deploy [options] show <config>
       deploy [options] graph <config>

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

# from https://www.tutorialspoint.com/insertion-sort-in-python-program
def insertionSort(arr):
   for i in range(1, len(arr)):
      key = arr[i]
      # Move elements of arr[0..i-1], that are greater than key,
      # to one position ahead of their current position
      j = i-1
      while j >=0 and key < arr[j] :
         arr[j+1] = arr[j]
         j -= 1
      arr[j+1] = key


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

    def __eq__(self, other):
        return self._package == other._package

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
        returns true if two packages do not have ordering depencies, i.e.
        neither depends (even indirectly) on the other.

        >>> A = Build("foo")
        >>> B = Build("bar", ["foo"])
        >>> A == B or B == A
        False
        >>> C = Build("baz")
        >>> A == C and C == A
        True

        Also having less specific dependencies causes non-parallel builds
        >>> A = Build("foo/1.2.3")
        >>> B = Build("bar", ["foo"])
        >>> A == B or B == A
        False
        '''
        result = not self < other and not other < self
        log.debug("compring %s %s %s", self, {True:"==", False:"<>"}[result], other)
        return result
        #return (self._package == other._package
        #       or
        #       ( self._package not in other._dependencies
        #         and other._package not in self._dependencies))

    def __repr__(self):
        return f'{self._package}(%s)' % "; ".join([str(d) for d in self._dependencies])

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

        Especially, undefined version/variant should always be built before:
        >>> D = Build("gcc", ['mpc'])
        >>> E = Build("gsl", ['gcc/10.2.0/default'])
        >>> D < E
        True
        >>> D > E
        False

        >>> A = Build("gcc", ["mpc"])
        >>> B = Build('boost', ['gcc/10.2.0'])
        >>> C = Build('gsl/2.6', ['gcc/10.2.0'])
        >>> A < B
        True
        >>> A < C
        True
        >>> B < A
        False
        >>> C < A
        False
        '''
        result = self._package in other._dependencies or any([self._package == dep for dep in other._dependencies])
        log.debug("compring %s %s %s", self, {True:"<", False:">="}[result], other)
        return result


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

class DotView:
    def __init__(self):
        self._default_node_attributes = {}
        self._default_edge_attributes = {}

    def attr(self, x, asep=', '):
        '''
        Return a dot formatted attribute string for the dictionary X

        Parameters
        ----------

        x : dictionary
            Key value pairs to be formatted as DOT attributes

        asep : str
            separator between different attributes

        Returns
        -------

        str : attributes formatted for DOT files

        Example
        -------

        >>> dot = DotView()
        >>> dot.attr({'label': 'boost/*/default'})
        'label="boost/*/default"'
        '''
        return asep.join([f'{k}="{v}"' for k,v in x.items()])

    def __call__(self, graph):
        name = "g"
        if "name" in graph:
            name = graph['name']
        output = ["digraph %s {" % name]

        output.append("    " + self.attr(graph.graph, asep="\n    "))
        output.append("\n    node [%s];" % self.attr(self._default_node_attributes))
        for node, data in graph.nodes(data=True):
            log.debug("node: %s (%s)", node, data)
        output.extend(['    {} [{}];'.format(n, self.attr(nattr)) for n, nattr in graph.nodes(data=True)])


        output.append("\n    edges [%s];" % self.attr(self._default_edge_attributes))
        for root in [node for node, degree in graph.in_degree() if degree == 0]:
            output.append("    // from %s" % graph.nodes[root]["label"])
            output.extend(['    {} -> {};'.format(*e) for e in networkx.algorithms.dfs_tree(graph, source=root).edges])
        output.append("}")
        return "\n".join(output)


import networkx
def GraphPresenter(deployment):
    '''
    Presents the build dependencies as a NetworkX graph object.

    Parameters
    ----------

    deployment : Deployment

        filled Deployment object.

    Returns
    -------

    networkx.DiGraph : dependency tree of all Builds in the deployment
    '''
    g = networkx.DiGraph(name="deps", title="Build Dependencies")
    nodeids = {}
    def nodeid(x):
        return nodeids.setdefault(repr(x), f"node{len(nodeids)}")

    def makenode(package):
        return (nodeid(package), {"label": repr(package)})

    g.add_nodes_from([makenode(build.package) for build in deployment._builds])

    for build in deployment._builds:
        g.add_nodes_from([makenode(dep) for dep in build.dependencies])     # required for non-built packages
        g.add_edges_from([(nodeid(build.package), nodeid(dep)) for dep in build.dependencies])

    log.info("Graph info:\n%s", networkx.classes.function.info(g))
    return g


class Deployment:
    '''
    Ordered set of Builds

    >>> d = Deployment([
    ...        Build("A", ["B"]),
    ...        Build("B", ["C"]),
    ...        Build("C", ["D"])
    ...     ])
    >>> list(d)
    [C/*/default(D/*/default), B/*/default(C/*/default), A/*/default(B/*/default)]

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
        for build in sorted(list(self._builds)):
            if any([build.package in donepkg.dependencies for donepkg in done]):
                log.error("building %s, but it has already been used by\n%s",
                          build,
                          [str(donepkg) for donepkg in done if build.package in donepkg.dependencies])
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
        [foo/*/default(), bar/*/default(foo/*/default; baz/*/default)]
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


# package > dependency:
# 02 nest-simulator/2.18.0/default(gsl/2.6/default; boost/1.74.0/default; cmake/*/default; mpi/*/default) >= cmake/*/default()
# 15 gcc/*/default(mpc/*/default) >= mpfr/*/default(gmp/*/default)
# 16 gcc/*/default(mpc/*/default) >= mpc/*/default(mpfr/*/default)
#
# package <> package:
# 01 cmake/*/default() >= boost/*/default(gcc/10.2.0/default)
# 03 nest-simulator/2.20.0/default(gsl/*/default; boost/1.74.0/default; cmake/*/default; mpi/*/default) >= nest-simulator/2.18.0/default(gsl/2.6/default; boost/1.74.0/default; cmake/*/default; mpi/*/default)
# 06 gsl/2.6/default(gcc/10.2.0/default) >= cmake/*/default()
#
# dependency < package (correct):
# 04 gsl/2.6/default(gcc/10.2.0/default) < nest-simulator/2.20.0/default(gsl/*/default; boost/1.74.0/default; cmake/*/default; mpi/*/default)
# 05 gsl/2.6/default(gcc/10.2.0/default) < nest-simulator/2.18.0/default(gsl/2.6/default; boost/1.74.0/default; cmake/*/default; mpi/*/default)
#
# dependency < package (wrong!):
# 07 gmp/*/default() >= gsl/2.6/default(gcc/10.2.0/default)
# 08 gmp/*/default() >= nest-simulator/2.20.0/default(gsl/*/default; boost/1.74.0/default; cmake/*/default; mpi/*/default)
# 09 mpfr/*/default(gmp/*/default) >= nest-simulator/2.18.0/default(gsl/2.6/default; boost/1.74.0/default; cmake/*/default; mpi/*/default)
# 10 mpfr/*/default(gmp/*/default) >= gmp/*/default()
# 11 mpc/*/default(mpfr/*/default) >= nest-simulator/2.18.0/default(gsl/2.6/default; boost/1.74.0/default; cmake/*/default; mpi/*/default)
# 12 mpc/*/default(mpfr/*/default) >= gmp/*/default()
# 13 mpc/*/default(mpfr/*/default) >= mpfr/*/default(gmp/*/default)
# 14 gcc/*/default(mpc/*/default) >= nest-simulator/2.20.0/default(gsl/*/default; boost/1.74.0/default; cmake/*/default; mpi/*/default)
#
# ERROR:root:building gcc/*/default(mpc/*/default), but it has already been used by
# ['boost/*/default(gcc/10.2.0/default)', 'gsl/2.6/default(gcc/10.2.0/default)']


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
        print(CommandsView(plan))
    elif args['graph']:
        dot = DotView()
        print(dot(GraphPresenter(plan)))

if __name__ == '__main__':
    main()
