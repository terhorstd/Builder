#!/usr/bin/env python
# encoding: utf8
#
#   Presenters.py – part of the "deploy" build automation system
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
Presenters module.

This module provides views with different representations of the loaded data.
'''
import logging
from textwrap import indent as text_indent

import networkx                                             # type: ignore
from networkx.classes.function import info as nx_info       # type: ignore

log = logging.getLogger(__name__)


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

        log.info("Graph info:\n%s", text_indent(nx_info(graph), "    "))
        return graph.reverse(copy=False)
