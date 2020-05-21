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
import asyncio
import json
import logging
import shutil
import subprocess
import sys

from pathlib import Path
from typing import Optional, Sequence, List

from mako.exceptions import RichTraceback
from tqdm import tqdm

from .collect import collect, specs_from_file, CollectError, SpecificationError
from .doxygenparser import Driver as ParserDriver
from .generator import process_adoc, AsciiDocError
from .model import json_repr
from ._version import __version__


def error(*args, **kwargs) -> None:
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def asciidoctor(destination_dir: Path, out_file: Path, processed_file: Path, multi_page: bool,
                backend: str, extra_args: Sequence[str]) -> None:
    subprocess.run([
        f"asciidoctor -D {destination_dir} -o {out_file} -b {backend} "
        f"{'-a multipage ' if multi_page else ''}"
        f"{processed_file} {' '.join(extra_args)}"
    ],
                   shell=True,
                   check=True)


def copy_and_switch_to_intermediate_dir(in_file: Path, adoc_dirs: List[Path],
                                        build_dir: Path) -> Path:
    intermediate_dir = build_dir / "intermediate"

    if intermediate_dir.exists():
        shutil.rmtree(intermediate_dir)

    shutil.copytree(str(in_file.parent), str(intermediate_dir))

    for adoc_dir in adoc_dirs:
        # workaround, in Python 3.8 we can call
        # `shutil.copytree(adoc_dir, intermediate_dir, dirs_exist_ok=True)`
        subprocess.run([f"cp -R {adoc_dir}/* {intermediate_dir}"], shell=True, check=True)

    return intermediate_dir / in_file.name


def output_extension(backend: str) -> Optional[str]:
    if backend == "html5":
        return ".html"
    elif backend == "pdf":
        return ".pdf"
    else:
        return None


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
    parser.add_argument("input_file", metavar="INPUT_FILE", help="Input AsciiDoc file.")
    parser.add_argument("-b",
                        "--backend",
                        metavar="BACKEND",
                        default="html5",
                        help="Set output backend format used by AsciiDoctor.")
    parser.add_argument("-B",
                        "--build-dir",
                        metavar="BUILD_DIR",
                        default="build",
                        help="Build directory.")
    parser.add_argument("-D",
                        "--destination-dir",
                        metavar="DESTINATION_DIR",
                        default=None,
                        help="Destination for generate documentation.")
    parser.add_argument("-s",
                        "--spec-file",
                        metavar="SPEC_FILE",
                        required=True,
                        help="Package specification file.")
    parser.add_argument("-v",
                        "--version-file",
                        metavar="VERSION_FILE",
                        default=None,
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
    parser.add_argument("--multi-page", action="store_true", help="Generate multi-page document.")
    if argv is None:
        argv = sys.argv[1:]
    args, extra_args = parser.parse_known_args(argv)

    log_level = getattr(logging, args.log)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    logger = logging.getLogger(__name__)

    build_dir = Path(args.build_dir).resolve()
    if args.destination_dir is not None:
        destination_dir = Path(args.destination_dir).resolve()
    else:
        destination_dir = build_dir / "output"
    spec_file = Path(args.spec_file).resolve()
    if args.version_file:
        version_file: Optional[Path] = Path(args.version_file).resolve()
    else:
        version_file = None

    extension = output_extension(args.backend)
    if extension is None:
        logger.error(f"Backend {args.backend} is not supported.")
        sys.exit(1)

    logger.info("Collecting packages  ")
    try:
        package_specs = specs_from_file(spec_file, version_file)
    except SpecificationError:
        logger.exception("Failed to load package specifications.")
        sys.exit(1)

    download_dir = build_dir / "download"
    try:
        with tqdm(desc="Collecting packages  ", total=len(package_specs), unit="pkg") as progress:
            packages = asyncio.get_event_loop().run_until_complete(
                collect(package_specs, download_dir, progress))
    except CollectError:
        logger.exception("Failed to collect packages.")
        sys.exit(1)

    logger.info("Loading packages")
    include_dirs: List[Path] = []
    xml_parser = ParserDriver(force_language=args.force_language)
    for pkg in tqdm(packages, desc="Loading API reference", unit="pkg"):
        include_dirs.extend(pkg.include_dirs)
        for xml_dir in pkg.xml_dirs:
            for xml_file in xml_dir.glob("**/*.xml"):
                xml_parser.parse(xml_file)

    with tqdm(desc="Resolving references ", unit="ref") as progress:
        xml_parser.resolve_references(progress)

    if args.debug:
        logger.info("Writing debug data, sorry for the delay!")
        with (build_dir / "debug.json").open("w", encoding="utf-8") as f:
            json.dump(xml_parser.api_reference.elements, f, default=json_repr, indent=2)

    in_file = copy_and_switch_to_intermediate_dir(
        Path(args.input_file).resolve(), include_dirs, build_dir)
    try:
        with tqdm(desc="Processing asciidoc  ", total=1, unit="file") as progress:
            in_to_out_file_map = process_adoc(in_file,
                                              build_dir,
                                              xml_parser.api_reference,
                                              warnings_are_errors=args.warnings_are_errors,
                                              multi_page=args.multi_page,
                                              progress=progress)

    except AsciiDocError as e:
        logger.error(f"Error while processing AsciiDoc file:\n\t{e}")
        logger.error("\nTraceback:")
        traceback = RichTraceback()
        for filename, lineno, _, line in traceback.traceback:
            if filename.endswith(".adoc"):
                logger.error(f"File {filename}, line {lineno}:\n\t{line}\n")
        sys.exit(1)

    logger.info("Running asciidoctor")
    in_dir = in_file.parent
    for (in_adoc_file, out_adoc_file) in tqdm(
        [(k, v) for (k, v) in in_to_out_file_map.items() if args.multi_page or k == in_file],
            desc="Running asciidoctor  ",
            unit="file"):
        out_file = destination_dir / in_adoc_file.relative_to(in_dir).with_suffix(extension)
        asciidoctor(destination_dir, out_file, out_adoc_file, args.multi_page, args.backend,
                    extra_args)
        logger.info(f"Generated: {out_file}")


if __name__ == "__main__":
    main()
