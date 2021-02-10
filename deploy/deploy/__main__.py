#!/usr/bin/env python
# encoding: utf8
#
#   __main__.py – part of the "deploy" build automation system
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

Usage: deploy [options] shell <config>
       deploy [options] gitlab <config>
       deploy [options] graph <config>
       deploy [options] deps <config>

  Deploy handles the organization of many build commands for a specific site
  when using the Builder tool.  As usually the Builds require prior loading of
  modules, and builds may be done in different variants, the complete software
  stack becomes difficult to track. Deploy manages a set of defined builds and
  can provide organizational overviews.

Subcommands are

  shell
    print the commands of all builds ordered by their dependencies for
    execution in a shell environment. Typical usage could be `deploy shell
    site.config > buildall.sh && ./buildall.sh`.

  gitlab
    print the build pipeline of all tools in a `.gitlab-ci.yml` includable
    format. The exact necessary syntax depends on the GitLab version, so tuning
    the template may be necessary.

  graph
    Print a DOT graph of the package dependencies to stdout. The resulting
    graph can be converted with Graphviz, for example:
        deploy.py graph site.config | dot -Tx11

Options:
    -v, --verbose       increase output
    -h, --help          print this text
'''
from pprint import pformat
import logging
from functools import wraps

from docopt import docopt                                   # type: ignore

from deploy import read_config, Deployment, Build
from deploy.presenters import GraphPresenter
from deploy.views import CommandsView, GitlabView, DotView, LineGraphView
from deploy.transforms.annotations import add_stage

log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


def add_transform(transform):
    def decorated(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return transform(func(*args, **kwargs))
        return wrapper
    return decorated


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
    graph = add_transform(add_stage)(graph)
    if args['shell']:
        commands = CommandsView()
        print(commands(graph(plan)))
    if args['gitlab']:
        gitlab = GitlabView()
        print(gitlab(graph(plan)))
    elif args['graph']:
        dot = DotView()
        print(dot(graph(plan)))
    elif args['deps']:
        view = LineGraphView()
        print(view(graph(plan)))


if __name__ == '__main__':
    main()
