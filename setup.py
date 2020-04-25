#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2019-2020, TomTom (http://tomtom.com).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The setup script."""

import os

from pathlib import Path
from setuptools import setup, find_packages

with open("README.adoc") as readme_file:
    readme = readme_file.read()

with open("CHANGELOG.adoc") as history_file:
    history = history_file.read()

requirements = ["mako~=1.1", "aiohttp~=3.6", "aiodns", "cchardet", "toml~=0.10"]

setup_requirements = ["pytest-runner>=5", ]

test_requirements = ["pytest>=4", ]

version = os.environ.get("WHEEL_VERSION", None)
if not version:
    version_file = Path(__file__).parent / "version.txt"
    if version_file.is_file():
        with version_file.open("r", encoding="utf-8") as f:
            minor_version = f.read()
        if minor_version:
            version = f"{minor_version.strip()}-dev"
    else:
        # Version file is not accessible from tox
        version = "0.0.0-dev"

setup(
    author="Rob van der Most",
    author_email="Rob.vanderMost@TomTom.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
    ],
    description="Generate AsciiDoc documentation from Doxygen XML output.",
    entry_points={
        "console_scripts": [
            "asciidoxy=asciidoxy.cli:main",
        ],
    },
    install_requires=requirements,
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="asciidoxy",
    name="asciidoxy",
    packages=find_packages(include=["asciidoxy", "asciidoxy.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://bitbucket.tomtomgroup.com/projects/NAVKIT2/repos/nk2-tools-asciidoxy",
    version=version,
    zip_safe=False,
)
