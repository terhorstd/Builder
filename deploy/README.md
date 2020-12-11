

Deploy
------

Deploy handles the organization of many build commands for a specific site when
using the Builder tool. As usually the Builds require prior loading of modules,
and builds may be done in different variants, the complete software stack
becomes difficult to track. Deploy manages a set of defined builds and can
provide organizational overviews.

This complements the dependency-less building process, by allowing to configure
exact dependencies for the target system. Dependency resolution outside of the
user-provided build configuration is left to the system, enabling maximum use
of system provided resources (e.g. in HPC environments).


Usage
-----

Deploy is based on a YAML input file specifying the builds to be executed by
Builder. The format is a simple dictionary of lists, where keys and values are
package strings. Each entry is a Build and required loaded modules.

```yaml
boost:
- gcc

cooltool:
- gcc
- boost
```

This file can be given as site config to `deploy`. To see available commands
run

```bash
deploy.py --help
```

The `show` subcommand is used to print all commands necessary for the full
deployment. You can inspect what would be done, or send output to a file and
use it as a deployment script.

```bash
deploy.py show site.config >build_all.sh
bash build_all.sh
```

Note that the actual build settings are configured with Builder's `.buildrc`.
See documentation of Builder for details.


Testing
-------

Run `pytest` to check package works as expected. For full testing, the test
environment requires

- pytest
- pytest-pylint
- pytest-mypy
- pytest-pycodestyle
- pytest-cov
- pytest-pydocstyle.

The configuration entry point is `tox.ini` which is recognized as config file
by various tools. PyLint branches out to `.pylintrc` as defined in `tox.ini`.

For the configuration options of each tool and the inline code configs see the
package specific documentation pages: [PyLint][pylint-doc], [MyPy][mypy-doc],
[PyCodeStyle][pycodestyle-doc], [PyDocStyle][pydocstyle-doc].

[pylint-doc]: http://pylint.pycqa.org/en/latest/faq.html?highlight=pylintrc#how-do-i-find-the-option-name-for-pylintrc-corresponding-to-a-specific-command-line-option PyLint Documentation
[mypy-doc]: https://mypy.readthedocs.io/en/latest/inline_config.html MyPy Documentation
[pycodestyle-doc]: https://pycodestyle.pycqa.org PyCodeStyle Documentation
[pydocstyle-doc]: http://www.pydocstyle.org/en/stable/usage.html?highlight=configuration#available-options PyDocStyle Documentation
[pytest-cov-doc]: https://pytest-cov.readthedocs.io PyTest-cov Documentation


License
-------

   deploy – build automation system
   Copyright (C) 2020  Dennis Terhorst

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.

