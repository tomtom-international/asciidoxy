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
"""Command line interface."""

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from mako.exceptions import RichTraceback
from tqdm import tqdm

from ._version import __version__
from .api_reference import ApiReference
from .asciidoctor import convert_documents
from .config import parse_args
from .generator import process_adoc
from .model import json_repr
from .packaging import CollectError, PackageManager, SpecificationError
from .parser.doxygen import Driver as DoxygenDriver


def error(*args, **kwargs) -> None:
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def main(argv: Optional[Sequence[str]] = None) -> None:
    print(rf"""
    ___              _ _ ____  {__version__:>16}
   /   |  __________(_|_) __ \____  _  ____  __
  / /| | / ___/ ___/ / / / / / __ \| |/_/ / / /
 / ___ |(__  ) /__/ / / /_/ / /_/ />  </ /_/ /
/_/  |_/____/\___/_/_/_____/\____/_/|_|\__, /
                                      /____/
""")

    config = parse_args(argv)

    log_level = getattr(logging, config.log)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    logger = logging.getLogger(__name__)

    pkg_mgr = PackageManager(config.build_dir, config.warnings_are_errors)
    if config.spec_file is not None:
        try:
            with tqdm(desc="Collecting packages     ", unit="pkg") as progress:
                pkg_mgr.collect(config.spec_file, config.version_file, progress)
        except SpecificationError:
            logger.exception("Failed to load package specifications.")
            sys.exit(1)
        except CollectError:
            logger.exception("Failed to collect packages.")
            sys.exit(1)

        xml_parser = DoxygenDriver(force_language=config.force_language)
        with tqdm(desc="Loading API reference   ", unit="pkg") as progress:
            pkg_mgr.load_reference(xml_parser, progress)

        with tqdm(desc="Resolving references    ", unit="ref") as progress:
            xml_parser.resolve_references(progress)

        if config.debug:
            logger.info("Writing debug data, sorry for the delay!")
            with (config.build_dir / "debug.json").open("w", encoding="utf-8") as f:
                json.dump(xml_parser.api_reference.elements, f, default=json_repr, indent=2)

        api_reference = xml_parser.api_reference
    else:
        api_reference = ApiReference()

    if config.backend == "adoc":
        pkg_mgr.work_dir = config.destination_dir
        clear_work_dir = False
    else:
        clear_work_dir = True
    pkg_mgr.set_input_files(config.input_file, config.base_dir, config.image_dir)
    with tqdm(desc="Preparing work directory", unit="pkg") as progress:
        in_doc = pkg_mgr.prepare_work_directory(config.input_file, clear_work_dir, progress)

    try:
        with tqdm(desc="Processing asciidoc     ", total=1, unit="file") as progress:
            documents = process_adoc(in_doc, api_reference, pkg_mgr, config, progress=progress)

    except:  # noqa: E722
        logger.error(human_traceback(pkg_mgr))
        sys.exit(1)

    if config.backend != "adoc":
        logger.info("Running AsciiDoctor...")
        convert_documents(documents, config, pkg_mgr)
    else:
        logger.info("Skipping AsciiDoctor")

    if config.backend != "pdf":
        with tqdm(desc="Copying images          ", unit="pkg") as progress:
            pkg_mgr.make_image_directory(config.destination_dir, progress)


def human_traceback(pkg_mgr: PackageManager) -> str:
    """Generate a human readable traceback the current exception. To be used inside an except
    clause.

    Exceptions triggered inside AsciiDoc are handled specially:
     - Lines inside AsciiDoc files are resolved to the original AsciiDoc lines.
     - AsciiDoxy code loading the AsciiDoc files is skipped.
     - Additional Mako loading due to includes is skipped.
    """
    traceback = RichTraceback()

    message = [""]
    has_adoc = False
    pending_traceback: List[str] = []
    for filename, lineno, function, line in traceback.traceback:
        if filename.endswith(".adoc"):
            pending_traceback.clear()

            package_name, original_file = pkg_mgr.find_original_file(Path(filename))
            if package_name and package_name != "INPUT":
                filename = f"{package_name}:/{original_file}"
            elif original_file is not None:
                filename = str(original_file)
            message.append(f"  File {filename}, line {lineno}, in AsciiDoc\n    {line}")
            has_adoc = True
        elif "/mako/" in filename:
            continue
        else:
            pending_traceback.append(f"  File {filename}, line {lineno}, in "
                                     f"{function}\n    {line}")
    if pending_traceback:
        message.extend(pending_traceback)

    if has_adoc:
        message[0] = f"Error while processing AsciiDoc files:\n{traceback.error}\nTraceback:"
    else:
        message[0] = f"Internal error:\n{traceback.error}\nTraceback:"

    return "\n".join(message)


if __name__ == "__main__":
    main()
