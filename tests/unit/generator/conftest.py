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

from collections import defaultdict
from itertools import combinations
from pathlib import Path

import pytest

from tests.unit.conftest import test_data_dir

_generated_data_dir = test_data_dir / "generated" / "adoc"


def pytest_sessionfinish(session: pytest.Session, exitstatus) -> None:
    if exitstatus == 0 and session.config.option.update_expected_results:
        _deduplicate_expected_results()


def _expected_result_file(name: Path, *specifiers: str) -> Path:
    """Complete expected result file name with all specifiers."""
    assert specifiers
    all_specifiers = ".".join(specifiers)
    return _generated_data_dir / f"{name}.{all_specifiers}.adoc"


def _updated_expected_result_file(name: Path, *specifiers: str) -> Path:
    """Name of the file to write updated results to."""
    return _expected_result_file(name, *specifiers).with_suffix(".update")


def _find_expected_result_file(name: Path, *specifiers: str) -> Path:
    """Find the best matching expected result file.

    The file matching the largest number of specifiers is selected.
    """
    assert specifiers
    for r in range(len(specifiers), 0, -1):
        for c in combinations(specifiers, r):
            combined_specs = ".".join(c)
            result_file = _generated_data_dir / f"{name}.{combined_specs}.adoc"
            if result_file.is_file():
                return result_file

    result_file = _generated_data_dir / f"{name}.adoc"
    if result_file.is_file():
        return result_file

    return _expected_result_file(name, *specifiers)


@pytest.fixture
def compare_to_file(request, doxygen_version):
    """Compare the actual content to the content of the best matching expected result file.

    If the command-line option `--update-expected-results` is given, the current content is stored
    instead of compared. The `sessionfinish` hook is used to deduplicate results again.
    """
    def check(name, actual_content: str, *extra_specifiers: str) -> None:
        name = Path(name)
        if request.config.getoption("update_expected_results"):
            result_file = _updated_expected_result_file(name, *extra_specifiers,
                                                        doxygen_version.replace(".", "_"))
            result_file.parent.mkdir(parents=True, exist_ok=True)
            result_file.write_text(actual_content, encoding="utf-8")
        else:
            expected_content = _find_expected_result_file(name, *extra_specifiers,
                                                          doxygen_version.replace(
                                                              ".", "_")).read_text(encoding="utf-8")
            assert actual_content == expected_content

    return check


def _group_similar_files(files):
    """Compare the content of a group of files and put the files with the same content together."""
    similar = []
    for result_file in files:
        content = result_file.read_text(encoding="utf-8")
        for other_files in similar:
            if other_files[0].read_text(encoding="utf-8") == content:
                other_files.append(result_file)
                break
        else:
            similar.append([result_file])
    return similar


def _common_name(files):
    """Find the common specifiers for a group of files."""
    common_parts = files[0].stem.split(".")

    for file in files[1:]:
        parts = file.stem.split(".")
        assert parts[0] == common_parts[0]
        common_parts = [part for part in common_parts if part in parts]

    name = ".".join(common_parts)
    return files[0].parent / f"{name}.adoc"


def _deduplicate_expected_results():
    """Deduplicate updated expected results.

    When updating expected results, each variant is stored separately. They need to be compared and
    duplicates removed.
    """
    grouped_files = defaultdict(list)
    for result_file in _generated_data_dir.glob("**/*.update"):
        base_name, _, _ = result_file.name.partition(".")
        if result_file.parent != _generated_data_dir:
            relative_path = result_file.parent.relative_to(_generated_data_dir)
            base_name = f"{relative_path}/{base_name}"
        grouped_files[base_name].append(result_file)

    for base_name, files in grouped_files.items():
        for old_file in _generated_data_dir.glob(f"{base_name}.*adoc"):
            old_file.unlink()

        similar = _group_similar_files(files)
        for group in sorted(similar, key=len, reverse=True):
            target_file = _common_name(group)
            if not target_file.is_file():
                group[0].rename(target_file)
                for obsolete_file in group[1:]:
                    obsolete_file.unlink()
            else:
                # Common name already in use by group with more matches
                for file in group:
                    file.rename(file.with_suffix(".adoc"))
