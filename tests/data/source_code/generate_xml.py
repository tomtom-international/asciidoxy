#!/usr/bin/env python3
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
"""Generate XML output from Doxygen for the test source code."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from subprocess import PIPE


def get_doxygen_version(doxygen: str) -> str:
    proc = subprocess.run([doxygen, "-v"], stdout=PIPE, encoding="utf-8", check=True)
    return proc.stdout.strip().split(" ", 1)[0]


def main() -> int:
    if len(sys.argv) != 2:
        print("Exactly one argument is required: path to the doxygen executable.", file=sys.stderr)
        return 1
    doxygen = sys.argv[1]
    version = get_doxygen_version(doxygen)
    print(f"Generating XML with doxygen version: {version}")

    xml_dir = (Path(__file__).parent / ".." / "generated" / "doxygen" / version).resolve()
    xml_dir.mkdir(parents=True, exist_ok=True)

    env = {key: value for key, value in os.environ.items()}
    for doxyfile in Path(__file__).parent.glob("**/Doxyfile*"):
        cwd = doxyfile.parent.resolve()
        out_dir = xml_dir / doxyfile.parent.relative_to(Path(__file__).parent)
        out_dir.mkdir(parents=True, exist_ok=True)

        env["OUTPUT_DIR"] = os.fspath(out_dir)
        subprocess.run([doxygen, os.fspath(doxyfile.resolve())], cwd=cwd, env=env, check=True)

        xml_out_dir = out_dir / "xml"
        image_dir = out_dir / "images"
        if image_dir.exists():
            shutil.rmtree(image_dir)
        image_dir.mkdir(parents=True, exist_ok=True)
        for image_file in xml_out_dir.glob("*.png"):
            shutil.move(image_file, image_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
