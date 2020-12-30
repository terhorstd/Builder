#!/usr/bin/env python
# encoding: utf8
#
#   views/CommandsView.py – part of the "deploy" build automation system
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
CommandsView module.

Format a given build dependency graph as executable code snippet. Builds are
ordered by dependencies and prefixed with required dependency loading.
'''
import logging

import networkx                                             # type: ignore
from networkx.algorithms.dag import topological_sort as nx_topological_sort     # type: ignore

from deploy import Build, Package
from deploy.views.ansi_colors import green, orange, gray, bold, blue

log = logging.getLogger(__name__)


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
