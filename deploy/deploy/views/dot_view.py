#!/usr/bin/env python
# encoding: utf8
#
#   views/DotView.py – part of the "deploy" build automation system
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
Graphviz DOT Language output module.

This module provides a view of a graph in DOT language notation that can be
parsed by tools like Graphviz.
'''
import logging

from networkx.algorithms import dfs_tree as nx_dfs_tree     # type: ignore

log = logging.getLogger(__name__)


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
