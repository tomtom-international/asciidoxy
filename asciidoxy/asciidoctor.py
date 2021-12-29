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
"""Running AsciiDoctor on the generated AsciiDoc files."""

import platform
import subprocess
from pathlib import Path
from typing import List

from .config import Configuration
from .document import Document
from .packaging import PackageManager
from .path_utils import relative_path


def generate_attributes(doc: Document, config: Configuration, pkg_mgr: PackageManager) -> str:
    image_dir = relative_path(doc.work_file, pkg_mgr.image_work_dir)
    values = [f"imagesdir@={image_dir}"]

    if config.multipage:
        values.append("multipage")

    values.extend(config.attribute)
    return " ".join(values)


def extension(backend: str) -> str:
    return {"html5": ".html", "pdf": ".pdf", "adoc": ".adoc"}[backend]


def generate_convert_file_command(doc: Document, config: Configuration,
                                  pkg_mgr: PackageManager) -> str:
    out_file = config.destination_dir / doc.relative_path.with_suffix(extension(config.backend))
    parts = [
        f"Asciidoctor.convert_file '{doc.work_file}'", f"to_file: '{out_file}'",
        f"safe: :{config.safe_mode.lower()}", f"backend: '{config.backend}'", "mkdirs: true",
        f"basedir: '{pkg_mgr.work_dir}'",
        f"attributes: '{generate_attributes(doc, config, pkg_mgr)}'"
    ]
    if config.doctype is not None:
        parts.append(f"doctype: '{config.doctype}'")
    return ", ".join(parts)


def generate_requires(config: Configuration) -> str:
    return "\n".join(f"require '{library}'" for library in ["asciidoctor"] + config.require)


def generate_exit_code(config: Configuration) -> str:
    return f"""\
logger = Asciidoctor::LoggerManager.logger
exit 1 if (logger.respond_to? :max_severity) &&
  logger.max_severity &&
  logger.max_severity >= (::Logger::Severity.const_get '{config.failure_level}')"""


def write_asciidoctor_runner(documents: List[Document], config: Configuration,
                             pkg_mgr: PackageManager) -> Path:
    runner_path = config.build_dir / "asciidoctor_runner.rb"
    with runner_path.open("w") as runner_file:
        print(generate_requires(config), file=runner_file)
        for doc in documents:
            if config.multipage and doc.is_embedded:
                continue
            if not config.multipage and not doc.is_root:
                continue
            print(generate_convert_file_command(doc, config, pkg_mgr), file=runner_file)
        print(generate_exit_code(config), file=runner_file)
    return runner_path


def run_ruby(script: Path) -> None:
    args = ["ruby", str(script)]
    if platform.system() == "Windows":
        subprocess.run(args, shell=True, check=True)
    else:
        subprocess.run(" ".join(args), shell=True, check=True)


def convert_documents(documents: List[Document], config: Configuration, pkg_mgr: PackageManager):
    run_ruby(write_asciidoctor_runner(documents, config, pkg_mgr))
