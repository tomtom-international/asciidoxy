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
"""Generic tests for parsing Doxygen XML files."""


def test_force_language_java(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", force_language="java")

    element = parser.api_reference.find("asciidoxy.traffic.TrafficEvent", kind="class", lang="java")
    assert element is not None
    assert element.language == "java"


def test_force_language_objc(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", force_language="objc")

    element = parser.api_reference.find("Logger", kind="class", lang="objc")
    assert element is not None
    assert element.language == "objc"


def test_force_language_unknown(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", force_language="unknown")

    element = parser.api_reference.find("asciidoxy::traffic::TrafficEvent",
                                        kind="class",
                                        lang="cpp")
    assert element is not None
    assert element.language == "cpp"


def test_force_language_empty(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", force_language="")

    element = parser.api_reference.find("asciidoxy::traffic::TrafficEvent",
                                        kind="class",
                                        lang="cpp")
    assert element is not None
    assert element.language == "cpp"
