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
"""Command line interface."""

import argparse
import json
import logging
import subprocess
import sys

from pathlib import Path
from typing import Optional, Sequence

from mako.exceptions import RichTraceback
from tqdm import tqdm

from .api_reference import ApiReference
from .generator import process_adoc, AsciiDocError
from .model import json_repr
from .packaging import CollectError, PackageManager, SpecificationError
from .parser.doxygen import Driver as DoxygenDriver
from ._version import __version__


def error(*args, **kwargs) -> None:
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def asciidoctor(destination_dir: Path, out_file: Path, processed_file: Path, multipage: bool,
                backend: str, extra_args: Sequence[str], image_dir: Path) -> None:
    subprocess.run([
        f"asciidoctor -D {destination_dir} -o {out_file} -b {backend} "
        f"{'-a multipage ' if multipage else ''}"
        f"-a imagesdir@={image_dir} "
        f"{processed_file} {' '.join(extra_args)}"
    ],
                   shell=True,
                   check=True)


def output_extension(backend: str) -> Optional[str]:
    if backend == "html5":
        return ".html"
    elif backend == "pdf":
        return ".pdf"
    else:
        return None


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


def main(argv: Optional[Sequence[str]] = None) -> None:
    print(rf"""
    ___              _ _ ____  {__version__:>16}
   /   |  __________(_|_) __ \____  _  ____  __
  / /| | / ___/ ___/ / / / / / __ \| |/_/ / / /
 / ___ |(__  ) /__/ / / /_/ / /_/ />  </ /_/ /
/_/  |_/____/\___/_/_/_____/\____/_/|_|\__, /
                                      /____/
""")

    parser = argparse.ArgumentParser(description="Generate API documentation using AsciiDoctor",
                                     allow_abbrev=False)
    parser.add_argument("input_file",
                        metavar="INPUT_FILE",
                        type=PathArgument(existing_file=True),
                        help="Input AsciiDoc file.")
    parser.add_argument("-B",
                        "--base-dir",
                        metavar="BASE_DIR",
                        default=None,
                        type=PathArgument(existing_dir=True),
                        help="Base directory containing the document and resources. If no base"
                        " directory is specified, local include files cannot be found.")
    parser.add_argument("--image-dir",
                        metavar="IMAGE_DIR",
                        default=None,
                        type=PathArgument(existing_dir=True),
                        help="Directory containing images to include. If no image directory is"
                        " specified, only images in the `images` directory next to the input file"
                        " can be included.")
    parser.add_argument("-b",
                        "--backend",
                        metavar="BACKEND",
                        default="html5",
                        help="Set output backend format used by AsciiDoctor.")
    parser.add_argument("--build-dir",
                        metavar="BUILD_DIR",
                        default="build",
                        type=PathArgument(new_dir=True),
                        help="Build directory.")
    parser.add_argument("-D",
                        "--destination-dir",
                        metavar="DESTINATION_DIR",
                        default=None,
                        type=PathArgument(new_dir=True),
                        help="Destination for generate documentation.")
    parser.add_argument("-s",
                        "--spec-file",
                        metavar="SPEC_FILE",
                        default=None,
                        type=PathArgument(existing_file=True),
                        help="Package specification file.")
    parser.add_argument("-v",
                        "--version-file",
                        metavar="VERSION_FILE",
                        default=None,
                        type=PathArgument(existing_file=True),
                        help="Version specification file.")
    parser.add_argument("-W",
                        "--warnings-are-errors",
                        action="store_true",
                        help="Stop processing input files when a warning is encountered.")
    parser.add_argument("--debug", action="store_true", help="Store debug information.")
    parser.add_argument("--log",
                        metavar="LOG_LEVEL",
                        default="WARNING",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the log level.")
    parser.add_argument("--force-language",
                        metavar="LANGUAGE",
                        help="Force language used when parsing doxygen XML files. Ignores the"
                        " language specified in the XML files.")
    parser.add_argument("--multipage", action="store_true", help="Generate multi-page document.")
    if argv is None:
        argv = sys.argv[1:]
    args, extra_args = parser.parse_known_args(argv)

    log_level = getattr(logging, args.log)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    logger = logging.getLogger(__name__)

    if args.destination_dir is not None:
        destination_dir = args.destination_dir
    else:
        destination_dir = args.build_dir / "output"
    extension = output_extension(args.backend)
    if extension is None:
        logger.error(f"Backend {args.backend} is not supported.")
        sys.exit(1)

    pkg_mgr = PackageManager(args.build_dir, args.warnings_are_errors)
    if args.spec_file is not None:
        try:
            with tqdm(desc="Collecting packages     ", unit="pkg") as progress:
                pkg_mgr.collect(args.spec_file, args.version_file, progress)
        except SpecificationError:
            logger.exception("Failed to load package specifications.")
            sys.exit(1)
        except CollectError:
            logger.exception("Failed to collect packages.")
            sys.exit(1)

        xml_parser = DoxygenDriver(force_language=args.force_language)
        with tqdm(desc="Loading API reference   ", unit="pkg") as progress:
            pkg_mgr.load_reference(xml_parser, progress)

        with tqdm(desc="Resolving references    ", unit="ref") as progress:
            xml_parser.resolve_references(progress)

        if args.debug:
            logger.info("Writing debug data, sorry for the delay!")
            with (args.build_dir / "debug.json").open("w", encoding="utf-8") as f:
                json.dump(xml_parser.api_reference.elements, f, default=json_repr, indent=2)

        api_reference = xml_parser.api_reference
    else:
        api_reference = ApiReference()

    pkg_mgr.set_input_files(args.input_file, args.base_dir, args.image_dir)
    with tqdm(desc="Preparing work directory", unit="pkg") as progress:
        in_file = pkg_mgr.prepare_work_directory(args.input_file, progress)

    try:
        with tqdm(desc="Processing asciidoc     ", total=1, unit="file") as progress:
            in_to_out_file_map = process_adoc(in_file,
                                              api_reference,
                                              pkg_mgr,
                                              warnings_are_errors=args.warnings_are_errors,
                                              multipage=args.multipage,
                                              progress=progress)

    except AsciiDocError as e:
        logger.error(f"Error while processing AsciiDoc file:\n\t{e}")
        logger.error("\nTraceback:")
        traceback = RichTraceback()
        for filename, lineno, _, line in traceback.traceback:
            if filename.endswith(".adoc"):
                logger.error(f"File {filename}, line {lineno}:\n\t{line}\n")
        sys.exit(1)

    in_dir = in_file.parent
    for (in_adoc_file, out_adoc_file) in tqdm(
        [(k, v) for (k, v) in in_to_out_file_map.items() if args.multipage or k == in_file],
            desc="Running asciidoctor     ",
            unit="file"):
        out_file = destination_dir / in_adoc_file.relative_to(in_dir).with_suffix(extension)
        asciidoctor(destination_dir, out_file, out_adoc_file, args.multipage, args.backend,
                    extra_args, pkg_mgr.image_work_dir)
        logger.info(f"Generated: {out_file}")

    if args.backend != "pdf":
        with tqdm(desc="Copying images          ", unit="pkg") as progress:
            pkg_mgr.make_image_directory(destination_dir, progress)


if __name__ == "__main__":
    main()
