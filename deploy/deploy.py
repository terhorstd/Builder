#!/usr/bin/env python
# encoding: utf8
#
#   deploy.py – build automation system
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
Organize a set of builds.

Usage: deploy [options] show <config>
       deploy [options] graph <config>

  Deploy handles the organization of many build commands for a specific site
  when using the Builder tool.  As usually the Builds require prior loading of
  modules, and builds may be done in different variants, the complete software
  stack becomes difficult to track. Deploy manages a set of defined builds and
  can provide organizational overviews.

Subcommands are

  show
     print the commands of all builds ordered by their dependencies.

  graph
    Print a DOT graph of the package dependencies to stdout. The resulting
    graph can be converted with Graphviz, for example:
        deploy.py graph site.config | dot -Tx11

Options:
    -v, --verbose       increase output
    -h, --help          print this text
'''
import sys
from pprint import pformat
from distutils.version import LooseVersion as Version
import logging
import networkx                                             # type: ignore
from networkx.classes.function import info as nx_info       # type: ignore
from networkx.algorithms import dfs_tree as nx_dfs_tree     # type: ignore
from networkx.algorithms.dag import topological_sort as nx_topological_sort     # type: ignore
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml import YAML
from docopt import docopt                                   # type: ignore

yaml = YAML()
log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


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


def red(text):
    'Format text.'
    return f"\033[31m{text}\033[m"


def green(text):
    'Format text.'
    return f"\033[32m{text}\033[m"


def blue(text):
    'Format text.'
    return f"\033[34m{text}\033[m"


def orange(text):
    'Format text.'
    return f"\033[00;33m{text}\033[m"


def yellow(text):
    'Format text.'
    return f"\033[00;33m{text}\033[m"


def gray(text):
    'Format text.'
    return f"\033[00;90m{text}\033[m"


def bold(text):
    'Format text.'
    return f"\033[01m{text}\033[m"


def nocolor(text):
    'Format text.'
    return text


if not sys.stdout.isatty():
    log.info("output to a non-tty.")
    red = nocolor
    green = nocolor
    blue = nocolor
    orange = nocolor
    yellow = nocolor
    gray = nocolor
    bold = nocolor


class CommandsView:     # pylint: disable=too-few-public-methods
    'View the commands required to build a complete package deployment graph.'

    def __call__(self, graph):
        'Return shell commands view of the given graph.'
        output = list()
        donepkgs = []
        assert isinstance(graph, networkx.DiGraph)
        for node in nx_topological_sort(graph):
            data = graph.nodes[node]
            if isinstance(data['item'], Build):
                build = data['item']
                output.extend(_template(build, donepkgs))
                donepkgs.append(build.package)

        return "\n".join(output) + "\n"


def _template(build, donepkgs=None):
    '''
    Write a commands section for the given build.

    Parameters
    ----------
    build : Build
        the build to fill the template with

    donepkgs : list
        list of Packages that preceed this build in a deployment
    '''
    if donepkgs is None:
        donepkgs = []
    output = []
    output.append(blue(f"\n# Building {build.package}"))
    output.append(gray("module purge"))
    for dep in build.dependencies:
        comment = blue("# ")
        info = gray("system provided")
        assert isinstance(dep, Package)
        if dep in donepkgs:
            info = green("just rebuilt")
        elif any([dep.name == done.name for done in donepkgs]):
            info = orange("maybe rebuilt")
        output.append(f"{dep.load_command:40s}{comment}{info}")
    output.append(bold(f"{build.package.build_command}"))
    return output


def dot_attr(adict, asep=', '):
    '''
    Return a dot formatted attribute string for the dictionary X.

    Parameters
    ----------
    adict : dictionary
        Key value pairs to be formatted as DOT attributes

    asep : str
        separator between different attributes

    Returns
    -------
    str : attributes formatted for DOT files

    Example
    -------
    >>> dot_attr({'label': 'boost/*/default'})
    'label="boost/*/default"'
    '''
    return asep.join([f'{key}="{val}"' for key, val in adict.items()])


class DotView:
    'View a package graph as DOT output.'

    def __init__(self):
        self._default_node_attributes = {}
        self._default_edge_attributes = {}
        self._label_format = "{pkg[label]}"

    def node_attr(self, attr):
        '''
        Produce graphviz-node style properties for package attributes.

        Parameters
        ----------
        attr : dict
            key value pairs representing the node attributes

        Returns
        -------
        dict : graphviz node style attributes
        '''
        style = {
            'label': self._label_format.format(pkg=attr),
        }
        if attr.get('type', "") == 'dep':
            style['style'] = 'dashed'
        return dot_attr(style)

    def __call__(self, graph):
        'Return DOT language view of the given graph.'
        name = "package_dependencies"
        graph.reverse(copy=False)
        if "name" in graph:
            name = graph['name']

        # graph level
        output = ["digraph %s {" % name]
        output.append("    " + dot_attr(graph.graph, asep="\n    "))

        # nodes
        # for node, data in graph.nodes(data=True):       # debug only
        #    log.debug("node: %d %s (%s)", nx_degree(graph, node), node, data)
        output.append("\n    node [%s];" % dot_attr(self._default_node_attributes))
        output.extend(['    {} [{}];'.format(n, self.node_attr(nattr)) for n, nattr in graph.nodes(data=True)])

        # edges
        output.append("\n    edge [%s];" % dot_attr(self._default_edge_attributes))
        for root in [node for node, degree in graph.in_degree() if degree == 0]:
            output.append("    // from %s" % graph.nodes[root]["label"])
            output.extend(['    {} -> {};'.format(*edge) for edge in nx_dfs_tree(graph, source=root).edges])
        output.append("}")
        return "\n".join(output)


class GraphPresenter:     # pylint: disable=too-few-public-methods
    'Presents the package build dependency graph of a Deployment.'

    def __call__(self, deployment):
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
        nodeids = {}

        def nodeid(name):
            return nodeids.setdefault(repr(name), f"node{len(nodeids)}")

        def makenode(package, **attr):
            attributes = {
                "label": repr(package),
                "name": package.name,
                "version": package.version,
                "variant": package.variant,
            }
            attributes.update(attr)
            return (nodeid(package), attributes)

        # graph
        graph = networkx.DiGraph(name="deps", title="Build Dependencies")

        # add `build.package`s
        graph.add_nodes_from([makenode(build.package, type="built", item=build) for build in deployment._builds])

        # add dependant packages and corresponding edges
        for build in deployment._builds:
            # required for non-built packages
            graph.add_nodes_from([makenode(dep, type="dep", item=dep)
                                  for dep in build.dependencies
                                  if not nodeid(dep) in graph.nodes])
            graph.add_edges_from([(nodeid(build.package), nodeid(dep)) for dep in build.dependencies])

        # add links between wildcard and special packages
        def nodes_with(key, value, graph):
            for node, data in graph.nodes(data=True):
                if data[key] != value:
                    continue
                yield node

        for wildnode in nodes_with('version', None, graph):
            for specnode in nodes_with('name', graph.nodes[wildnode]['name'], graph):
                if graph.nodes[specnode]['version'] is None:
                    continue
                graph.add_edge(specnode, wildnode, type="induced")

        log.info("Graph info:\n%s", nx_info(graph))
        return graph.reverse(copy=False)


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


def main():
    'Run CLI entry point.'
    args = docopt(__doc__)
    if args['--verbose']:
        log.setLevel(logging.DEBUG)
    log.debug(pformat(args))

    log.info("deploy.py (Dennis Terhorst, GPLv3)")

    config = read_config(args['<config>'])

    plan = Deployment()
    for package, dependencies in config.items():
        plan.append(Build(package, dependencies))

    graph = GraphPresenter()
    if args['show']:
        commands = CommandsView()
        print(commands(graph(plan)))
    elif args['graph']:
        dot = DotView()
        print(dot(graph(plan)))


if __name__ == '__main__':
    main()
