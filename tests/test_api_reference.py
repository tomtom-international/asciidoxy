# Copyright (C) 2019-2021, TomTom (http://tomtom.com).
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
"""Tests for API reference storage and search."""

import pytest

from asciidoxy.api_reference import AmbiguousLookupError, NameFilter, ParameterTypeMatcher
from asciidoxy.parser.doxygen import Driver as ParserDriver


def test_function_matcher__parse__no_arguments():
    ptm = ParameterTypeMatcher("method")
    assert ptm.name == "method"
    assert ptm.arg_types is None

    ptm = ParameterTypeMatcher("namespace::method")
    assert ptm.name == "namespace::method"
    assert ptm.arg_types is None

    ptm = ParameterTypeMatcher("com.namespace.method")
    assert ptm.name == "com.namespace.method"
    assert ptm.arg_types is None


def test_function_matcher__parse__zero_arguments():
    ptm = ParameterTypeMatcher("method()")
    assert ptm.name == "method"
    assert ptm.arg_types == []

    ptm = ParameterTypeMatcher("namespace::method()")
    assert ptm.name == "namespace::method"
    assert ptm.arg_types == []

    ptm = ParameterTypeMatcher("com.namespace.method()")
    assert ptm.name == "com.namespace.method"
    assert ptm.arg_types == []


def test_function_matcher__parse__one_argument():
    ptm = ParameterTypeMatcher("method(int)")
    assert ptm.name == "method"
    assert ptm.arg_types == ["int"]

    ptm = ParameterTypeMatcher("namespace::method(std::string)")
    assert ptm.name == "namespace::method"
    assert ptm.arg_types == ["std::string"]

    ptm = ParameterTypeMatcher("com.namespace.method(id<std::string>)")
    assert ptm.name == "com.namespace.method"
    assert ptm.arg_types == ["id<std::string>"]


def test_function_matcher__parse__multiple_arguments():
    ptm = ParameterTypeMatcher("method(int, string)")
    assert ptm.name == "method"
    assert ptm.arg_types == ["int", "string"]

    ptm = ParameterTypeMatcher("namespace::method(std::string, bool, Element)")
    assert ptm.name == "namespace::method"
    assert ptm.arg_types == ["std::string", "bool", "Element"]

    ptm = ParameterTypeMatcher("com.namespace.method(id<std::string>, vector<Class>)")
    assert ptm.name == "com.namespace.method"
    assert ptm.arg_types == ["id<std::string>", "vector<Class>"]


def test_function_matcher__parse__multiple_nested_args():
    ptm = ParameterTypeMatcher("method(std::vector<Type, Alloc>)")
    assert ptm.name == "method"
    assert ptm.arg_types == ["std::vector<Type,Alloc>"]


def test_function_matcher__parse__normalize_whitespace():
    ptm = ParameterTypeMatcher(" method( )")
    assert ptm.name == "method"
    assert ptm.arg_types == []

    ptm = ParameterTypeMatcher("namespace::method ()")
    assert ptm.name == "namespace::method"
    assert ptm.arg_types == []

    ptm = ParameterTypeMatcher("com.namespace.method()  ")
    assert ptm.name == "com.namespace.method"
    assert ptm.arg_types == []

    ptm = ParameterTypeMatcher("method( int )")
    assert ptm.name == "method"
    assert ptm.arg_types == ["int"]

    ptm = ParameterTypeMatcher("namespace::method ( std::string)")
    assert ptm.name == "namespace::method"
    assert ptm.arg_types == ["std::string"]

    ptm = ParameterTypeMatcher("namespace : : method (std: :string)")
    assert ptm.name == "namespace::method"
    assert ptm.arg_types == ["std::string"]

    ptm = ParameterTypeMatcher("com.namespace.method(id< std::string>) ")
    assert ptm.name == "com.namespace.method"
    assert ptm.arg_types == ["id<std::string>"]

    ptm = ParameterTypeMatcher("method( int , string )")
    assert ptm.name == "method"
    assert ptm.arg_types == ["int", "string"]


class FullNameObject:
    def __init__(self, name):
        self.full_name = name


def test_name_filter__name_only__no_namespace_in_name():
    nf = NameFilter("MyClass")
    assert nf.applies

    assert nf(FullNameObject("MyClass")) is True
    assert nf(FullNameObject("NotMyClass")) is False
    assert nf(FullNameObject("MyClassNeither")) is False
    assert nf(FullNameObject("definitely::not::MyClass")) is False
    assert nf(FullNameObject("not::MyClass::either")) is False


def test_name_filter__name_only__namespace_in_name():
    nf = NameFilter("com.mypackage.MyClass")
    assert nf.applies

    assert nf(FullNameObject("com.mypackage.MyClass")) is True
    assert nf(FullNameObject("mypackage.MyClass")) is False
    assert nf(FullNameObject("MyClass")) is False
    assert nf(FullNameObject("org.mypackage.MyClass")) is False
    assert nf(FullNameObject("com.asciidoxy.MyClass")) is False
    assert nf(FullNameObject("com.mypackage.MyClass.SubClass")) is False


def test_name_filter__namespace__exact_match():
    nf = NameFilter("Coordinate", namespace="asciidoxy::geometry")
    assert nf.applies

    assert nf(FullNameObject("asciidoxy::geometry::Coordinate")) is True
    assert nf(FullNameObject("asciidoxy::traffic::Coordinate")) is False
    assert nf(FullNameObject("sphinx::geometry::Coordinate")) is False
    assert nf(FullNameObject("asciidoxy::geometry::Point")) is False
    assert nf(FullNameObject("asciidoxy::geometry::Coordinate::Type")) is False
    assert nf(FullNameObject("com::asciidoxy::geometry::Coordinate")) is False


def test_name_filter__namespace__partial_namespace_in_name():
    nf = NameFilter("geometry::Coordinate", namespace="asciidoxy")
    assert nf.applies

    assert nf(FullNameObject("asciidoxy::geometry::Coordinate")) is True
    assert nf(FullNameObject("asciidoxy::traffic::Coordinate")) is False
    assert nf(FullNameObject("sphinx::geometry::Coordinate")) is False
    assert nf(FullNameObject("asciidoxy::geometry::Point")) is False
    assert nf(FullNameObject("asciidoxy::geometry::Coordinate::Type")) is False
    assert nf(FullNameObject("com::asciidoxy::geometry::Coordinate")) is False


def test_name_filter__namespace__partial_overlap():
    nf = NameFilter("geometry::Coordinate", namespace="asciidoxy::geometry")
    assert nf.applies

    assert nf(FullNameObject("asciidoxy::geometry::Coordinate")) is True
    assert nf(FullNameObject("asciidoxy::geometry::geometry::Coordinate")) is True
    assert nf(FullNameObject("geometry::Coordinate")) is True
    assert nf(FullNameObject("asciidoxy::Coordinate")) is False
    assert nf(FullNameObject("asciidoxy::geometry::experimental::geometry::Coordinate")) is False


def test_name_filter__namespace__namespace_in_parent_namespace():
    nf = NameFilter("geometry::Coordinate", namespace="asciidoxy::traffic")
    assert nf.applies

    assert nf(FullNameObject("asciidoxy::geometry::Coordinate")) is True
    assert nf(FullNameObject("asciidoxy::traffic::geometry::Coordinate")) is True
    assert nf(FullNameObject("asciidoxy::geometry::traffic::Coordinate")) is False


def test_name_filter__namespace__exact_namespace_required():
    nf = NameFilter("geometry::Coordinate", namespace="asciidoxy::traffic", exact_namespace=True)
    assert nf.applies

    assert nf(FullNameObject("asciidoxy::geometry::Coordinate")) is False
    assert nf(FullNameObject("asciidoxy::traffic::geometry::Coordinate")) is True
    assert nf(FullNameObject("asciidoxy::geometry::traffic::Coordinate")) is False


def test_name_filter__namespace__exact_namespace_required__same_name():
    nf = NameFilter("Coordinate", namespace="asciidoxy::geometry::Coordinate", exact_namespace=True)
    assert nf.applies

    assert nf(FullNameObject("asciidoxy::geometry::Coordinate")) is False
    assert nf(FullNameObject("asciidoxy::geometry::Coordinate::Coordinate")) is True


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_complete_match(api_reference):
    assert api_reference.find("asciidoxy::geometry::Coordinate", kind="function",
                              lang="cpp") is None
    assert api_reference.find("asciidoxy::geometry::Coordinate", kind="class", lang="java") is None
    assert api_reference.find(
        "asciidoxy::geometry::Coordinate::Coordinate", kind="class", lang="cpp") is None
    assert api_reference.find("asciidoxy::geometry::Coordinate", kind="class",
                              lang="cpp") is not None


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_only_by_id(api_reference):
    assert api_reference.find(target_id="cpp-classasciidoxy_1_1geometry_1_1_coordinate") is not None


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_only_by_name(api_reference):
    assert api_reference.find("asciidoxy::geometry::Coordinate") is not None


def test_find_by_name_and_kind(test_data):
    parser = ParserDriver()
    parser.parse(test_data / "ambiguous_names.xml")

    element = parser.api_reference.find("Coordinate", kind="class")
    assert element is not None
    assert element.kind == "class"

    element = parser.api_reference.find("Coordinate", kind="interface")
    assert element is not None
    assert element.kind == "interface"

    assert parser.api_reference.find("Coordinate", kind="function") is None


def test_find_by_name_and_lang(test_data):
    parser = ParserDriver()
    parser.parse(test_data / "ambiguous_names.xml")

    element = parser.api_reference.find("BoundingBox", lang="java")
    assert element is not None
    assert element.language == "java"

    element = parser.api_reference.find("BoundingBox", lang="objc")
    assert element is not None
    assert element.language == "objc"

    assert parser.api_reference.find("BoundingBox", lang="cpp") is None


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_by_name_and_namespace(api_reference):
    assert api_reference.find("asciidoxy::geometry::Coordinate", namespace="asciidoxy") is not None
    assert api_reference.find("geometry::Coordinate", namespace="asciidoxy") is not None

    assert api_reference.find("asciidoxy::geometry::Coordinate",
                              namespace="asciidoxy::geometry") is not None
    assert api_reference.find("geometry::Coordinate", namespace="asciidoxy::geometry") is not None
    assert api_reference.find("Coordinate", namespace="asciidoxy::geometry") is not None

    assert api_reference.find("asciidoxy::geometry::Coordinate",
                              namespace="asciidoxy::traffic") is not None
    assert api_reference.find("geometry::Coordinate", namespace="asciidoxy::traffic") is not None


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_by_name__prefer_exact_match(api_reference):
    assert api_reference.find("asciidoxy::geometry::Coordinate::Coordinate",
                              namespace="asciidoxy").namespace == "asciidoxy::geometry::Coordinate"

    assert api_reference.find(
        "Coordinate",
        namespace="asciidoxy::geometry::Coordinate").namespace == "asciidoxy::geometry::Coordinate"

    assert api_reference.find("asciidoxy::geometry::Coordinate",
                              namespace="asciidoxy").namespace == "asciidoxy::geometry"
    assert api_reference.find("Coordinate",
                              namespace="asciidoxy::geometry").namespace == "asciidoxy::geometry"


def test_find_by_name_ambiguous(test_data):
    parser = ParserDriver()
    parser.parse(test_data / "ambiguous_names.xml")

    with pytest.raises(AmbiguousLookupError) as exception1:
        parser.api_reference.find("BoundingBox")
    assert len(exception1.value.candidates) == 2

    with pytest.raises(AmbiguousLookupError) as exception2:
        parser.api_reference.find("Coordinate", lang="cpp")
    assert len(exception2.value.candidates) == 2


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_by_name__overload_set(api_reference):
    element = api_reference.find("asciidoxy::to_string", allow_overloads=True)
    assert element is not None
    assert element.kind == "function"
    assert element.namespace == "asciidoxy"

    element = api_reference.find("asciidoxy::traffic::to_string", allow_overloads=True)
    assert element is not None
    assert element.kind == "function"
    assert element.namespace == "asciidoxy::traffic"

    element = api_reference.find("to_string", namespace="asciidoxy", allow_overloads=True)
    assert element is not None
    assert element.kind == "function"
    assert element.namespace == "asciidoxy"

    element = api_reference.find("to_string", namespace="asciidoxy::traffic", allow_overloads=True)
    assert element is not None
    assert element.kind == "function"
    assert element.namespace == "asciidoxy::traffic"

    element = api_reference.find("to_string", namespace="asciidoxy::geometry", allow_overloads=True)
    assert element is not None
    assert element.kind == "function"
    assert element.namespace == "asciidoxy"


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_by_name__overload_set__multiple_namespaces_are_ambiguous(api_reference):
    with pytest.raises(AmbiguousLookupError) as exception:
        api_reference.find("to_string",
                           namespace="asciidoxy::traffic::geometry",
                           allow_overloads=True)
    assert len(exception.value.candidates) == 3


def test_find_by_name__overload_set__multiple_kinds_are_ambiguous(test_data):
    parser = ParserDriver()
    parser.parse(test_data / "ambiguous_names.xml")

    with pytest.raises(AmbiguousLookupError) as exception:
        parser.api_reference.find("StringType", allow_overloads=True)
    assert len(exception.value.candidates) == 3

    element = parser.api_reference.find("StringType", allow_overloads=True, kind="class")
    assert element is not None
    assert element.kind == "class"

    element = parser.api_reference.find("StringType", allow_overloads=True, kind="enum")
    assert element is not None
    assert element.kind == "enum"

    element = parser.api_reference.find("StringType", allow_overloads=True, kind="interface")
    assert element is not None
    assert element.kind == "interface"


def test_find_by_name__overload_set__multiple_languages_are_ambiguous(test_data):
    parser = ParserDriver()
    parser.parse(test_data / "ambiguous_names.xml")

    with pytest.raises(AmbiguousLookupError) as exception:
        parser.api_reference.find("BoundingBox", allow_overloads=True)
    assert len(exception.value.candidates) == 2

    element = parser.api_reference.find("BoundingBox", allow_overloads=True, lang="java")
    assert element is not None
    assert element.language == "java"

    element = parser.api_reference.find("BoundingBox", allow_overloads=True, lang="objc")
    assert element is not None
    assert element.language == "objc"


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_method__explicit_no_arguments(api_reference):
    element = api_reference.find("asciidoxy::geometry::Coordinate::Coordinate()")
    assert element is not None


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_method__explicit_no_arguments__requires_no_args(api_reference):
    element = api_reference.find("asciidoxy::traffic::TrafficEvent::Update()")
    assert element is None


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_method__select_based_on_args(api_reference):
    with pytest.raises(AmbiguousLookupError):
        api_reference.find("asciidoxy::traffic::TrafficEvent::TrafficEvent")

    element = api_reference.find("asciidoxy::traffic::TrafficEvent::TrafficEvent()")
    assert element is not None

    element = api_reference.find("asciidoxy::traffic::TrafficEvent::TrafficEvent(TrafficEventData)")
    assert element is not None


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_find_method__select_based_on_args_2(api_reference):
    with pytest.raises(AmbiguousLookupError):
        api_reference.find("asciidoxy::geometry::Coordinate::Update")

    element = api_reference.find("asciidoxy::geometry::Coordinate::Update()")
    assert element is None

    element = api_reference.find("asciidoxy::geometry::Coordinate::Update(const Coordinate&)")
    assert element is not None

    element = api_reference.find(
        "asciidoxy::geometry::Coordinate::Update(std::tuple< double, double, double >)")
    assert element is not None

    element = api_reference.find(
        "asciidoxy::geometry::Coordinate::Update(std::tuple< double, double >)")
    assert element is not None

    element = api_reference.find("asciidoxy::geometry::Coordinate::Update(double, double)")
    assert element is not None

    element = api_reference.find("asciidoxy::geometry::Coordinate::Update(double, double, double)")
    assert element is not None
