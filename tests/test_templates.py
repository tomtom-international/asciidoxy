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
"""Test the templates used for C++ code."""

import os
import pytest

from pathlib import Path


def _read_fragment(include_statement: str) -> str:
    prefix_end = len("include::")
    suffix_begin = include_statement.index("[")

    file_name = Path(include_statement[prefix_end:suffix_begin])
    assert file_name.is_file()

    content = file_name.read_text(encoding="UTF-8")
    assert content
    return content


@pytest.mark.parametrize(
    "element_name,expected_result",
    [("asciidoxy::geometry::Coordinate", "fragments/cpp/class.adoc"),
     ("asciidoxy::traffic::TrafficEvent::Severity", "fragments/cpp/enum.adoc"),
     ("asciidoxy::system::Service", "fragments/cpp/interface.adoc"),
     ("asciidoxy::traffic::TrafficEvent::TrafficEventData", "fragments/cpp/struct.adoc"),
     ("asciidoxy::traffic::TpegCauseCode", "fragments/cpp/typedef.adoc"),
     ("asciidoxy::traffic::TrafficEvent", "fragments/cpp/nested.adoc"),
     ("com.asciidoxy.geometry.Coordinate", "fragments/java/class.adoc"),
     ("com.asciidoxy.traffic.TrafficEvent.Severity", "fragments/java/enum.adoc"),
     ("com.asciidoxy.system.Service", "fragments/java/interface.adoc"),
     ("com.asciidoxy.traffic.TrafficEvent", "fragments/java/nested.adoc"),
     ("ADTrafficEvent", "fragments/objc/protocol.adoc"),
     ("TrafficEventData.ADSeverity", "fragments/objc/enum.adoc"),
     ("ADCoordinate", "fragments/objc/interface.adoc"),
     ("OnTrafficEventCallback", "fragments/objc/block.adoc"),
     ("TpegCauseCode", "fragments/objc/typedef.adoc")])
def test_fragment(api, adoc_data, fragment_dir, element_name, expected_result,
                  update_expected_results):
    result = api.insert(element_name)
    content = _read_fragment(result)
    content = content.replace(os.fspath(fragment_dir), "DIRECTORY")

    if update_expected_results:
        (adoc_data / expected_result).write_text(content, encoding="UTF-8")

    assert content == (adoc_data / expected_result).read_text(encoding="UTF-8")


filtered_testdata = [("asciidoxy::geometry::Coordinate", {
    "members": "-Altitude"
}, "fragments/cpp/class_filtered.adoc"),
                     ("asciidoxy::traffic::TrafficEvent::Severity", {
                         "enum_values": ["+Medium", "+High"]
                     }, "fragments/cpp/enum_filtered.adoc"),
                     ("asciidoxy::system::Service", {
                         "members": "+Start"
                     }, "fragments/cpp/interface_filtered.adoc"),
                     ("asciidoxy::traffic::TrafficEvent::TrafficEventData", {
                         "members": "-delay"
                     }, "fragments/cpp/struct_filtered.adoc"),
                     ("asciidoxy::traffic::TrafficEvent", {
                         "inner_classes": ["+Severity", "-TrafficEventData"]
                     }, "fragments/cpp/nested_filtered.adoc"),
                     ("com.asciidoxy.geometry.Coordinate", {
                         "members": "-IsValid"
                     }, "fragments/java/class_filtered.adoc"),
                     ("com.asciidoxy.traffic.TrafficEvent.Severity", {
                         "members": "-Unknown"
                     }, "fragments/java/enum_filtered.adoc"),
                     ("com.asciidoxy.system.Service", {
                         "members": "Start"
                     }, "fragments/java/interface_filtered.adoc"),
                     ("com.asciidoxy.traffic.TrafficEvent", {
                         "inner_classes": "TrafficEventData"
                     }, "fragments/java/nested_filtered.adoc"),
                     ("ADTrafficEvent", {
                         "members": {
                             "kind": "-property"
                         }
                     }, "fragments/objc/protocol_filtered.adoc"),
                     ("TrafficEventData.ADSeverity", {
                         "enum_values": ["Low", "Medium"]
                     }, "fragments/objc/enum_filtered.adoc"),
                     ("ADCoordinate", {
                         "members": {
                             "kind": "property"
                         }
                     }, "fragments/objc/interface_filtered.adoc")]


@pytest.mark.parametrize("element_name,filter_spec,expected_result", filtered_testdata)
def test_global_filter(api, adoc_data, fragment_dir, element_name, filter_spec, expected_result,
                       update_expected_results):
    api.filter(**filter_spec)
    result = api.insert(element_name)
    content = _read_fragment(result)
    content = content.replace(os.fspath(fragment_dir), "DIRECTORY")

    if update_expected_results:
        (adoc_data / expected_result).write_text(content, encoding="UTF-8")

    assert content == (adoc_data / expected_result).read_text(encoding="UTF-8")


@pytest.mark.parametrize("element_name,filter_spec,expected_result", filtered_testdata)
def test_local_filter(api, adoc_data, fragment_dir, element_name, filter_spec, expected_result,
                      update_expected_results):
    result = api.insert(element_name, **filter_spec)
    content = _read_fragment(result)
    content = content.replace(os.fspath(fragment_dir), "DIRECTORY")

    if update_expected_results:
        (adoc_data / expected_result).write_text(content, encoding="UTF-8")

    assert content == (adoc_data / expected_result).read_text(encoding="UTF-8")
