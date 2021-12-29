# Copyright (C) 2019, TomTom (http://tomtom.com).
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
"""Configuration for running AsciiDoxy."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional


class PathArgument:
    _existing_dir: bool
    _existing_file: bool
    _new_dir: bool

    def __init__(self,
                 existing_dir: bool = False,
                 existing_file: bool = False,
                 new_dir: bool = False):
        self._existing_dir = existing_dir
        self._existing_file = existing_file
        self._new_dir = new_dir

    def __call__(self, value: str) -> Optional[Path]:
        if value is None:
            return None

        path = Path(value).resolve()

        if self._existing_dir and not path.is_dir():
            raise argparse.ArgumentTypeError(
                "{} does not point to an existing directory.".format(value))
        if self._existing_file and not path.is_file():
            raise argparse.ArgumentTypeError("{} does not point to an existing file.".format(value))
        if self._new_dir and path.is_file():
            raise argparse.ArgumentTypeError("{} points to an existing file.".format(value))
        if not self._new_dir and not path.parent.exists():
            raise argparse.ArgumentTypeError(
                "Directory to store {} in does not exist.".format(value))

        return path


class Configuration(argparse.Namespace):
    """Configuration options for running AsciiDoxy.

    Populated from the command-line arguments and extended to include sensible default values.
    """
    input_file: Path

    base_dir: Optional[Path] = None
    image_dir: Optional[Path] = None
    spec_file: Optional[Path] = None
    version_file: Optional[Path] = None

    build_dir: Path
    destination_dir: Path
    template_dir: Optional[Path] = None
    cache_dir: Path

    backend: str
    warnings_are_errors: bool
    debug: bool
    log_level: str
    force_language: Optional[str] = None
    multipage: bool

    safe_mode: str
    attribute: List[str]
    doctype: Optional[str]
    require: List[str]
    failure_level: str


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Generate API documentation using AsciiDoctor",
                                     allow_abbrev=False)
    input_group = parser.add_argument_group(title="Specifying input resources")
    input_group.add_argument("input_file",
                             metavar="INPUT_FILE",
                             type=PathArgument(existing_file=True),
                             help="Input AsciiDoc file.")
    input_group.add_argument("-B",
                             "--base-dir",
                             metavar="BASE_DIR",
                             default=None,
                             type=PathArgument(existing_dir=True),
                             help="Base directory containing the document and resources. If no base"
                             " directory is specified, local include files cannot be found.")
    input_group.add_argument(
        "--image-dir",
        metavar="IMAGE_DIR",
        default=None,
        type=PathArgument(existing_dir=True),
        help="Directory containing images to include. If no image directory is"
        " specified, only images in the `images` directory next to the input file"
        " can be included.")

    external_data_group = parser.add_argument_group(title="Loading external data")
    external_data_group.add_argument("-s",
                                     "--spec-file",
                                     metavar="SPEC_FILE",
                                     default=None,
                                     type=PathArgument(existing_file=True),
                                     help="Package specification file.")
    external_data_group.add_argument("-v",
                                     "--version-file",
                                     metavar="VERSION_FILE",
                                     default=None,
                                     type=PathArgument(existing_file=True),
                                     help="Version specification file.")

    output_group = parser.add_argument_group(title="Controlling output")
    output_group.add_argument("--build-dir",
                              metavar="BUILD_DIR",
                              default="build",
                              type=PathArgument(new_dir=True),
                              help="Build directory.")
    output_group.add_argument("-D",
                              "--destination-dir",
                              metavar="DESTINATION_DIR",
                              default=None,
                              type=PathArgument(new_dir=True),
                              help="Destination for generated documentation.")
    output_group.add_argument(
        "-b",
        "--backend",
        metavar="BACKEND",
        default="html5",
        choices=["html5", "pdf", "adoc"],
        help="Set output backend format used by AsciiDoctor. Use special backend"
        " `adoc` to produce AsciiDoc files only and not run AsciiDoctor on it.")

    behavior_group = parser.add_argument_group(title="AsciiDoxy behavior")
    behavior_group.add_argument("--multipage",
                                action="store_true",
                                help="Generate multi-page document.")
    behavior_group.add_argument("-W",
                                "--warnings-are-errors",
                                action="store_true",
                                help="Stop processing input files when a warning is encountered.")
    behavior_group.add_argument(
        "--force-language",
        metavar="LANGUAGE",
        help="Force language used when parsing doxygen XML files. Ignores the"
        " language specified in the XML files.")
    behavior_group.add_argument(
        "--cache-dir",
        metavar="CACHE_DIR",
        default=None,
        type=PathArgument(new_dir=True),
        help="Directory for caching generated python code for templates and input"
        " documents. Reduces runtime for consecutive runs by skipping code"
        "generation for unchanged files.")

    asciidoctor_group = parser.add_argument_group(
        title="AsciiDoctor options",
        description="These options are not used by AsciiDoxy itself, but are used to"
        " run AsciiDoctor. See AsciiDoctor documentation for details.")
    asciidoctor_group.add_argument("-S",
                                   "--safe-mode",
                                   metavar="SAFE_MODE",
                                   default="unsafe",
                                   choices=["unsafe", "safe", "server", "secure"],
                                   help="Set safe mode level.")
    asciidoctor_group.add_argument("-a",
                                   "--attribute",
                                   metavar="ATTRIBUTE",
                                   action="append",
                                   type=str,
                                   default=[],
                                   help="Define, override, or unset a document attribute.")
    asciidoctor_group.add_argument("-d",
                                   "--doctype",
                                   metavar="DOCTYPE",
                                   default=None,
                                   choices=["article", "book", "manpage", "inline"],
                                   help="Set the document type.")
    asciidoctor_group.add_argument(
        "-r",
        "--require",
        metavar="LIBRARY",
        action="append",
        type=str,
        default=[],
        help="Require the specified library before executing AsciiDoctor.")
    asciidoctor_group.add_argument(
        "--failure-level",
        metavar="LEVEL",
        default="FATAL",
        choices=["FATAL", "ERROR", "WARN"],
        help="Set the minimum log level that results in a failure for AsciiDoctor.")

    debug_group = parser.add_argument_group(title="Debugging AsciiDoxy")
    debug_group.add_argument("--debug", action="store_true", help="Store debug information.")
    debug_group.add_argument("--log",
                             metavar="LOG_LEVEL",
                             default="WARNING",
                             choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                             help="Set the log level.")

    experimental_group = parser.add_argument_group(title="Experimental features",
                                                   description="Use at your own risk!")
    experimental_group.add_argument(
        "--template-dir",
        metavar="TEMPLATE_DIR",
        default=None,
        type=PathArgument(existing_dir=True),
        help="Directory containing custom templates to use instead"
        " of the default templates shipped with AsciiDoxy. Templates found in this"
        " directory will be used in favor of the default templates. Only when a"
        " template is not found here, the default templates are used.")
    if argv is None:
        argv = sys.argv[1:]

    config = Configuration()
    config = parser.parse_args(argv, namespace=config)

    if config.destination_dir is None:
        config.destination_dir = config.build_dir / "output"
    if config.cache_dir is None:
        config.cache_dir = config.build_dir / "cache"

    return config
