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

from asciidoxy._version import (__title__, __description__, __url__, __version__, __author__,
                                __author_email__, __license__)

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = [
    "mako~=1.1",
    "aiohttp~=3.6",
    "aiodns",
    "cchardet",
    "toml~=0.10",
    "tqdm~=4.46",
    "packaging~=20.3",
]

setup_requirements = [
    "pytest-runner>=5",
]

test_requirements = [
    "pytest>=4",
]

setup(
    author=__author__,
    author_email=__author_email__,
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
    ],
    description=__description__,
    entry_points={
        "console_scripts": [
            "asciidoxy=asciidoxy.cli:main",
        ],
    },
    install_requires=requirements,
    long_description=readme,
    long_description_content_type="text/markdown",
    license=__license__,
    include_package_data=True,
    keywords="asciidoxy",
    name=__title__,
    packages=find_packages(include=["asciidoxy", "asciidoxy.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url=__url__,
    project_urls={
        "Documentation": "https://asciidoxy.org",
        "Bug Tracker": "https://github.com/tomtom-international/asciidoxy/issues",
        "Source Code": "https://github.com/tomtom-international/asciidoxy",
    },
    version=__version__,
    zip_safe=False,
)
