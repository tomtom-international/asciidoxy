```
    ___              _ _ ____
   /   |  __________(_|_) __ \____  _  ____  __
  / /| | / ___/ ___/ / / / / / __ \| |/_/ / / /
 / ___ |(__  ) /__/ / / /_/ / /_/ />  </ /_/ /
/_/  |_/____/\___/_/_/_____/\____/_/|_|\__, /
                                      /____/
```

[ [Home](https://asciidoxy.org) |
[What is AsciiDoxy?](https://asciidoxy.org/about.html) |
[Usage](https://asciidoxy.org/usage.html) |
[Examples](https://asciidoxy.org/examples.html) |
[Contributing](https://asciidoxy.org/contributing.html) |
[Changelog](CHANGELOG.adoc) |
[GitHub](https://github.com/tomtom-international/asciidoxy) ]

[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![pip downloads](https://img.shields.io/pypi/dm/asciidoxy)](https://pypi.org/project/asciidoxy)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/asciidoxy)](https://pypi.org/project/asciidoxy)
[![PyPI](https://img.shields.io/pypi/v/asciidoxy)](https://pypi.org/project/asciidoxy)

AsciiDoxy generates API documentation from [Doxygen](https://doxygen.nl) XML output to AsciiDoc.

Supported languages:
- C++
- Java
- Objective C
- Python (using [doxypypy](https://github.com/Feneric/doxypypy))

Features:

- API documentation generation.
- Collecting API reference information from remote and local sources.
- Single and multi page HTML output.
- Single page PDF output.


## Credits

Inspiration for creating AsciiDoxy was found in this article by Sy Brand:
https://devblogs.microsoft.com/cppblog/clear-functional-c-documentation-with-sphinx-breathe-doxygen-cmake/

Before going public on GitHub, several people inside [TomTom](https://www.tomtom.com) contributed to
the internal version of AsciiDoxy. Many thanks to:

- Andy Salter
- Arkadiusz Skalski
- Lukasz Glowcyk
- Nebojsa Mrmak
- Niels van der Schans
- Robert Gernert
- Tomasz Maj

The python package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
