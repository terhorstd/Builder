#!/usr/bin/env python
# encoding: utf8
'''
Module to fill templates.

The templates are automatically chosen by class name.
'''
import sys
import datetime
import logging
from dataclasses import dataclass, field
from typing import Optional
# from docopt import docopt                                   # type: ignore
from pathlib import Path
# from ruamel.yaml import YAML
from jinja2 import Environment, FileSystemLoader
# from jinja2 import select_autoescape

log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


class TemplateView:     # pylint: disable=too-few-public-methods
    'View based on filling Jinja2 templates.'

    def __init__(self, templatedir="templates"):
        'Initialize template loader with given path.'
        self._templatedir = Path(__file__).parents[0] / Path(templatedir)

        log.debug("template directory '%s'", self._templatedir)
        self._env = Environment(
            loader=FileSystemLoader(str(self._templatedir)),
            trim_blocks=True,
            lstrip_blocks=True,
            # autoescape=select_autoescape(['html', 'xml'])
            extensions=[
                'jinja2.ext.loopcontrols',
            ],
        )

        if not self._env.list_templates():
            log.error("NO TEMPLATES FOUND in %s/!", self._templatedir)
            raise RuntimeError("No templates found in %s/" % self._templatedir)
        log.debug("available templates: %s", self._env.list_templates())
        # add custom filters
        # newfilters = loadfilters(args['--filter'])
        # log.debug("new filters: %s", newfilters)
        # env.filters.update(newfilters)
        self._env.filters.update({'render': self})

    def __call__(self, obj):
        'Return rendered template filled with given data.'
        classname = type(obj).__name__
        log.debug("render object of type %s", classname)
        tname = classname + ".j2"
        # load template
        tmplate = self._env.get_template(tname)
        return tmplate.render(obj=obj, context={"datetime": datetime.datetime.now()})


@dataclass
class Task:
    'AST presentation object.'

    name: str = field(default="unnamed")


@dataclass
class If:
    'AST presentation object.'

    condition: str
    then_block: Task
    else_block: Optional[Task] = None


def main():
    'CLI entrypoint.'
    # some dummy data
    # data = [
    #    {'name': 'foo', 'depth': 1, 'dependencies': [], 'script': ['module load x; build y;']},
    #    {'name': 'bar', 'depth': 2, 'dependencies': ["foo", "goo", "hoo"]},
    # ]
    data = If(condition="1+1=2", then_block=Task("correct"), else_block=Task("wrong"))
    data2 = If(condition="2+2=4", then_block=Task("correct"))

    view = TemplateView()

    # output result
    ostream = sys.stdout
    # if args['--output'] is not None:
    #    ostream = open(args['--output'], 'w')
    log.info("writing output to %s", ostream.name)
    with ostream as outfile:
        outfile.write(view(data))
        outfile.write(view(data2))


if __name__ == '__main__':
    main()
