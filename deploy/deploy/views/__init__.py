#!/usr/bin/env python
# encoding: utf8
#
#   views/__init__.py – part of the "deploy" build automation system
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
Views package.

Output adapters for various formats.
'''
from deploy.views.gitlab_view import GitlabView
from deploy.views.commands_view import CommandsView
from deploy.views.dot_view import DotView
from deploy.views.line_graph_view import LineGraphView
