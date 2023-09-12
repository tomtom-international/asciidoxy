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
"""Test the templates used for C++ code."""

import pytest

from tests.unit.api_reference_loader import ApiReferenceLoader


@pytest.fixture(scope="module")
def api_reference(all_doxygen_versions):
    return ApiReferenceLoader().version(all_doxygen_versions).load_all()


@pytest.mark.parametrize("element_name,language,expected_result", [
    ("asciidoxy::geometry::Coordinate", "cpp", "fragments/cpp/class"),
    ("asciidoxy::traffic::TrafficEvent::Severity", "cpp", "fragments/cpp/enum"),
    ("asciidoxy::system::Service", "cpp", "fragments/cpp/interface"),
    ("asciidoxy::traffic::TrafficEvent::TrafficEventData", "cpp", "fragments/cpp/struct"),
    ("asciidoxy::traffic::TpegCauseCode", "cpp", "fragments/cpp/alias"),
    ("asciidoxy::traffic::Delay", "cpp", "fragments/cpp/typedef"),
    ("DEFAULT_CB", "cpp", "fragments/cpp/function_typedef"),
    ("asciidoxy::wifi::ESP32WiFiProtocol", "cpp", "fragments/cpp/enum_with_or"),
    ("asciidoxy::traffic::TrafficEvent", "cpp", "fragments/cpp/nested"),
    ("asciidoxy::traffic::TrafficEvent::SharedData", "cpp", "fragments/cpp/function"),
    ("asciidoxy::system::CreateService", "cpp", "fragments/cpp/free_function"),
    ("asciidoxy::geometry::Point::increment", "cpp", "fragments/cpp/function_default_value"),
    ("asciidoxy::tparam::IsEven", "cpp", "fragments/cpp/function_tparam"),
    ("asciidoxy::tparam::Mapping", "cpp", "fragments/cpp/class_tparam"),
    ("com.asciidoxy.geometry.Coordinate", "java", "fragments/java/class"),
    ("com.asciidoxy.traffic.TrafficEvent.Severity", "java", "fragments/java/enum"),
    ("com.asciidoxy.system.Service", "java", "fragments/java/interface"),
    ("com.asciidoxy.traffic.TrafficEvent", "java", "fragments/java/nested"),
    ("ADTrafficEvent", "objc", "fragments/objc/protocol"),
    ("ADSeverity", "objc", "fragments/objc/enum"),
    ("ADCoordinate", "objc", "fragments/objc/interface"),
    ("OnTrafficEventCallback", "objc", "fragments/objc/block"),
    ("TpegCauseCode", "objc", "fragments/objc/typedef"),
    ("asciidoxy.geometry.Coordinate", "python", "fragments/python/class"),
    ("asciidoxy.traffic.TrafficEvent.update", "python", "fragments/python/function"),
    ("asciidoxy.default_values.Point.increment", "python",
     "fragments/python/function_default_value"),
])
def test_fragment(generating_api, element_name, language, expected_result, compare_to_file):
    content = generating_api.insert(element_name, lang=language)
    compare_to_file(expected_result, content)


filtered_testdata = [
    ("asciidoxy::geometry::Coordinate", "cpp", {
        "members": {
            "name": "-Altitude",
            "prot": "ALL"
        }
    }, "fragments/cpp/class_filtered"),
    ("asciidoxy::traffic::TrafficEvent::Severity", "cpp", {
        "members": ["+Medium", "+High"]
    }, "fragments/cpp/enum_filtered"),
    ("asciidoxy::system::Service", "cpp", {
        "members": "+Start"
    }, "fragments/cpp/interface_filtered"),
    ("asciidoxy::traffic::TrafficEvent::TrafficEventData", "cpp", {
        "members": "-delay"
    }, "fragments/cpp/struct_filtered"),
    ("asciidoxy::traffic::TrafficEvent", "cpp", {
        "members": {
            "prot": "ALL",
            "name": "-TrafficEventData",
        },
    }, "fragments/cpp/nested_filtered"),
    ("asciidoxy::traffic::TrafficEvent::SharedData", "cpp", {
        "exceptions": "-std::"
    }, "fragments/cpp/function_filtered"),
    ("com.asciidoxy.geometry.Coordinate", "java", {
        "members": "-IsValid"
    }, "fragments/java/class_filtered"),
    ("com.asciidoxy.traffic.TrafficEvent.Severity", "java", {
        "members": "-Unknown"
    }, "fragments/java/enum_filtered"),
    ("com.asciidoxy.system.Service", "java", {
        "members": "Start"
    }, "fragments/java/interface_filtered"),
    ("com.asciidoxy.traffic.TrafficEvent", "java", {
        "members": "-Severity"
    }, "fragments/java/nested_filtered"),
    ("ADTrafficEvent", "objc", {
        "members": {
            "kind": "-property"
        }
    }, "fragments/objc/protocol_filtered"),
    ("ADSeverity", "objc", {
        "members": ["Low", "Medium"]
    }, "fragments/objc/enum_filtered"),
    ("ADCoordinate", "objc", {
        "members": {
            "kind": "property"
        }
    }, "fragments/objc/interface_filtered"),
    ("asciidoxy.geometry.Coordinate", "python", {
        "members": "-altitude"
    }, "fragments/python/class_filtered"),
    ("asciidoxy.traffic.TrafficEvent.refresh_data", "python", {
        "exceptions": "NoDataError",
    }, "fragments/python/function_filtered"),
]


@pytest.mark.parametrize("element_name,language,filter_spec,expected_result", filtered_testdata)
def test_global_filter(generating_api, element_name, language, filter_spec, expected_result,
                       compare_to_file):
    generating_api.filter(**filter_spec)
    content = generating_api.insert(element_name, lang=language)
    compare_to_file(expected_result, content)


@pytest.mark.parametrize("element_name,language,filter_spec,expected_result", filtered_testdata)
def test_local_filter(generating_api, element_name, language, filter_spec, expected_result,
                      compare_to_file):
    content = generating_api.insert(element_name, lang=language, **filter_spec)
    compare_to_file(expected_result, content)


@pytest.mark.parametrize("element_name,source,target,expected_result", [
    ("ADTrafficEvent", "objc", "swift", "fragments/swift/transcoded_protocol"),
    ("ADSeverity", "objc", "swift", "fragments/swift/transcoded_enum"),
    ("ADCoordinate", "objc", "swift", "fragments/swift/transcoded_interface"),
    ("OnTrafficEventCallback", "objc", "swift", "fragments/swift/transcoded_block"),
    ("TpegCauseCode", "objc", "swift", "fragments/swift/transcoded_typedef"),
    ("com.asciidoxy.geometry.Coordinate", "java", "kotlin", "fragments/kotlin/transcoded_class"),
    ("com.asciidoxy.traffic.TrafficEvent.Severity", "java", "kotlin",
     "fragments/kotlin/transcoded_enum"),
    ("com.asciidoxy.system.Service", "java", "kotlin", "fragments/kotlin/transcoded_interface"),
    ("com.asciidoxy.traffic.TrafficEvent", "java", "kotlin", "fragments/kotlin/transcoded_nested"),
])
def test_transcoded_fragment(generating_api, element_name, source, target, expected_result,
                             compare_to_file):
    generating_api.language(target, source=source)
    content = generating_api.insert(element_name)
    compare_to_file(expected_result, content)
