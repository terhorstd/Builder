#!/usr/bin/env python
# encoding: utf8
#
#   views/GitlabView.py – part of the "deploy" build automation system
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
GitlabView module.

View a given build dependency graph as GitLab-CI staged configuration file. The
resulting output can be imported to any ``.gitlab-ci.yml`` to build the given
software stack.
'''
import logging

import networkx                                             # type: ignore

from deploy.views.templview import TemplateView

log = logging.getLogger(__name__)


class GitlabView:     # pylint: disable=too-few-public-methods
    'View the commands required to build a complete package deployment graph.'

    def __call__(self, graph):
        'Return shell commands view of the given graph.'
        assert isinstance(graph, networkx.DiGraph)
        view = TemplateView()
        return view(graph)
