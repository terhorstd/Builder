#!/usr/bin/env python
# encoding: utf8
#
#   transforms/annotations.py – part of the "deploy" build automation system
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
Annotations module.

This module holds functions to annotate graph node data objects with structural
data.  The data can subsequently be used in views.r
'''
import networkx

def add_stage(graph: networkx.DiGraph) -> networkx.DiGraph:
    '''
    Add the "stage" property to the Builds (inplace).

    The build stage corresponds to the maximum depht of a build in the DAG.
    '''
    for node in graph.nodes:
        data = graph.nodes[node]
        data["stage"] = "unknown"
    return graph
