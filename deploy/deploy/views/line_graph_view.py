#!/usr/bin/env python
# encoding: utf8
#
#   views/LineGraphView.py – part of the "deploy" build automation system
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
Console graph output module.

This module provides a view to represent DAGs in an ASCII-art for console
output (actually it's UTF-8 art…).
'''
import logging
from typing import Optional, Tuple, Sequence

import networkx                                             # type: ignore

log = logging.getLogger(__name__)


class LineGraphView:    # pylint: disable=too-few-public-methods
    'View graph with indentions and one node per line.'

    def __init__(self, nodeformat='{node[label]} {node[stage]}'):
        self._nodeformat = nodeformat
        self._lines = {
            "default": {
                "branch": (" ├─╴", " │  "),   # branch, forward
                "last": (" ╰─╴", "    "),
            },
            "dashed": {
                "branch": ("▶├┄ ", " │  "),   # branch, forward
                "last": ("▶╰┄ ", "    "),
            },
        }

    def __call__(self, graph, root: Optional[str] = None, indent: str = "") -> str:
        'Return line graph view of the given graph.'
        assert isinstance(graph, networkx.DiGraph)
        if root is None:
            roots = [(node, None) for node, degree in graph.in_degree() if degree == 0]
        else:
            roots = [(root, None)]
        return "\n".join(self._subtree(graph, roots))

    def _subtree(self, graph, roots: Sequence[Tuple[str, Optional[str]]], indent=""):
        '''
        Generate lines for each subtree.

        Parameters
        ----------
        graph : networkx.DiGraph
        roots : list (optional)
            optional list of tuples with root nodes to draw. List items must be
            pairs of node and praent edge pointing to each node. It is assumed
            that there is exactly one parent edge per node.
        indent : string (optional)
            prefix of each line
        '''
        for node, edge in roots:
            lines = self._lines["default"]
            nodedata = graph.nodes[node]
            edgedata = None
            if edge is not None:
                edgedata = graph.edges[edge, node]
                if edgedata.get("type", 'unknown') == 'induced':
                    lines = self._lines["dashed"]

            branch, forward = lines["branch"]
            if node == roots[-1][0]:    # last
                branch, forward = lines["last"]
            yield indent + branch + self._nodeformat.format(node=nodedata, edge=edgedata)
            yield from self._subtree(
                graph,
                roots=[(child, edge) for edge, child in graph.edges(node)],
                indent=indent + forward)
