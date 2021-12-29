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
"""Utilities for working with paths."""

from pathlib import Path


def relative_path(from_file: Path, to_file: Path):
    assert from_file.is_absolute()
    assert to_file.is_absolute()

    path = Path()
    for ancestor in from_file.parents:
        try:
            path = path / to_file.relative_to(ancestor)
            break
        except ValueError:
            path = path / '..'

    return path
