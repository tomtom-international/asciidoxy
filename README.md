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
[Getting started](https://asciidoxy.org/getting-started.html) |
[Reference documentation](https://asciidoxy.org/reference.html) |
[Examples](https://asciidoxy.org/examples.html) |
[Contributing](https://asciidoxy.org/contributing.html) |
[Changelog](CHANGELOG.adoc) |
[GitHub](https://github.com/tomtom-international/asciidoxy) ]

[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![pip downloads](https://img.shields.io/pypi/dm/asciidoxy)](https://pypi.org/project/asciidoxy)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/asciidoxy)](https://pypi.org/project/asciidoxy)
[![PyPI](https://img.shields.io/pypi/v/asciidoxy)](https://pypi.org/project/asciidoxy)

AsciiDoxy generates API documentation from [Doxygen](https://doxygen.nl) XML output to AsciiDoc.
[AsciiDoctor](https://asciidoctor.org) is then used to create HTML or PDF documentation that can be
published online.

Supported languages:
- C++
- Java
- Objective-C
- Python (using [doxypypy](https://github.com/Feneric/doxypypy))
- Swift (transcoded from Objective-C only)
- Kotlin (transcoded from Java only)

Features:

- API documentation generation.
- Collecting API reference information from remote and local sources.
- Single and multipage HTML output.
- Single page PDF output.
- Transcoding: showing how to use elements written in one language in another compatible language.


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
