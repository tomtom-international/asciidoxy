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
"""Tests for API reference storage and search."""

import pytest

from asciidoxy.api_reference import (
    AmbiguousLookupError,
    ApiReference,
    NameFilter,
    ParameterTypeMatcher,
)
from asciidoxy.parser import parser_factory
from tests.unit.api_reference_loader import ApiReferenceLoader
from tests.unit.shared import ProgressMock


@pytest.fixture(scope="module")
def api_reference(latest_doxygen_version):
    return ApiReferenceLoader().version(latest_doxygen_version).add("doxygen", "cpp/default").load()


@pytest.fixture(scope="function")
def unresolved_api_reference(latest_doxygen_version):
    return ApiReferenceLoader().version(latest_doxygen_version).add("doxygen", "cpp/default").add(
        "doxygen", "cpp/consumer").load(resolve_references=False)


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


def test_name_filter__namespace__nested_name():
    nf = NameFilter("geometry::Coordinate<geometry::Point>", namespace="asciidoxy::geometry")
    assert nf.applies

    assert nf(FullNameObject("asciidoxy::geometry::Coordinate<geometry::Point>")) is True
    assert nf(FullNameObject("asciidoxy::geometry::geometry::Coordinate<geometry::Point>")) is True
    assert nf(FullNameObject("geometry::Coordinate<geometry::Point>")) is True
    assert nf(FullNameObject("asciidoxy::Coordinate<geometry::Point>")) is False
    assert nf(
        FullNameObject(
            "asciidoxy::geometry::experimental::geometry::Coordinate<geometry::Point>")) is False
    assert nf(FullNameObject("asciidoxy::geometry::Coordinate<>")) is False
    assert nf(FullNameObject("asciidoxy::geometry::Coordinate")) is False
    assert nf(FullNameObject("asciidoxy::geometry::Coordinate<geometry::Dot>")) is False


def test_find_complete_match(api_reference):
    assert api_reference.find("asciidoxy::geometry::Coordinate", kind="function",
                              lang="cpp") is None
    assert api_reference.find("asciidoxy::geometry::Coordinate", kind="class", lang="java") is None
    assert api_reference.find(
        "asciidoxy::geometry::Coordinate::Coordinate", kind="class", lang="cpp") is None
    assert api_reference.find("asciidoxy::geometry::Coordinate", kind="class",
                              lang="cpp") is not None


def test_find_only_by_id(api_reference):
    assert api_reference.find(target_id="cpp-classasciidoxy_1_1geometry_1_1_coordinate") is not None


def test_find_only_by_name(api_reference):
    assert api_reference.find("asciidoxy::geometry::Coordinate") is not None


def test_find_by_name_with_spaces(api_reference):
    assert api_reference.find("asciidoxy::tparam::is_container< std::array< T, N> >") is not None
    assert api_reference.find("asciidoxy::tparam::is_container<std::array<T,N>>") is not None
    assert api_reference.find("asciidoxy ::tparam::is_container<std::array<T,N>>") is not None
    assert api_reference.find("asciidoxy:: tparam::is_container<std::array<T,N>>") is not None
    assert api_reference.find("asciidoxy::tparam ::is_container<std::array<T,N>>") is not None
    assert api_reference.find("asciidoxy::tparam:: is_container<std::array<T,N>>") is not None
    assert api_reference.find("asciidoxy::tparam::is_container <std::array<T,N>>") is not None
    assert api_reference.find("asciidoxy::tparam::is_container< std::array<T,N>>") is not None
    assert api_reference.find("asciidoxy::tparam::is_container<std::array <T,N>>") is not None
    assert api_reference.find("asciidoxy::tparam::is_container<std::array<T,N >>") is not None

    assert api_reference.find("is_container<std::array<T,N>>",
                              namespace="asciidoxy::tparam") is not None
    assert api_reference.find(" is_container<std::array<T,N>>",
                              namespace="asciidoxy::tparam") is not None
    assert api_reference.find("is_container <std::array<T,N>>",
                              namespace="asciidoxy::tparam") is not None
    assert api_reference.find("is_container< std::array<T,N>>",
                              namespace="asciidoxy::tparam") is not None
    assert api_reference.find("is_container<std::array <T,N>>",
                              namespace="asciidoxy::tparam") is not None
    assert api_reference.find("is_container<std::array< T,N>>",
                              namespace="asciidoxy::tparam") is not None
    assert api_reference.find("is_container<std::array<T ,N>>",
                              namespace="asciidoxy::tparam") is not None
    assert api_reference.find("is_container<std::array<T, N>>",
                              namespace="asciidoxy::tparam") is not None
    assert api_reference.find("is_container<std::array<T,N >>",
                              namespace="asciidoxy::tparam") is not None
    assert api_reference.find("is_container<std::array<T,N> >",
                              namespace="asciidoxy::tparam") is not None


def test_find_by_name_and_kind(test_data):
    parser = parser_factory("doxygen", ApiReference())
    parser.parse(test_data / "ambiguous_names.xml")

    element = parser.api_reference.find("Coordinate", kind="class")
    assert element is not None
    assert element.kind == "class"

    element = parser.api_reference.find("Coordinate", kind="interface")
    assert element is not None
    assert element.kind == "interface"

    assert parser.api_reference.find("Coordinate", kind="function") is None


def test_find_by_name_and_lang(test_data):
    parser = parser_factory("doxygen", ApiReference())
    parser.parse(test_data / "ambiguous_names.xml")

    element = parser.api_reference.find("BoundingBox", lang="java")
    assert element is not None
    assert element.language == "java"

    element = parser.api_reference.find("BoundingBox", lang="objc")
    assert element is not None
    assert element.language == "objc"

    assert parser.api_reference.find("BoundingBox", lang="cpp") is None


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
    parser = parser_factory("doxygen", ApiReference())
    parser.parse(test_data / "ambiguous_names.xml")

    with pytest.raises(AmbiguousLookupError) as exception1:
        parser.api_reference.find("BoundingBox")
    assert len(exception1.value.candidates) == 2

    with pytest.raises(AmbiguousLookupError) as exception2:
        parser.api_reference.find("Coordinate", lang="cpp")
    assert len(exception2.value.candidates) == 2


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


def test_find_by_name__overload_set__multiple_namespaces_are_ambiguous(api_reference):
    with pytest.raises(AmbiguousLookupError) as exception:
        api_reference.find("to_string",
                           namespace="asciidoxy::traffic::geometry",
                           allow_overloads=True)
    assert len(exception.value.candidates) == 3


def test_find_by_name__overload_set__multiple_kinds_are_ambiguous(test_data):
    parser = parser_factory("doxygen", ApiReference())
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
    parser = parser_factory("doxygen", ApiReference())
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


def test_find_method__explicit_no_arguments(api_reference):
    element = api_reference.find("asciidoxy::geometry::Coordinate::Coordinate()")
    assert element is not None


def test_find_method__explicit_no_arguments__requires_no_args(api_reference):
    element = api_reference.find("asciidoxy::traffic::TrafficEvent::Update()")
    assert element is None


def test_find_method__select_based_on_args(api_reference):
    with pytest.raises(AmbiguousLookupError):
        api_reference.find("asciidoxy::traffic::TrafficEvent::TrafficEvent")

    element = api_reference.find("asciidoxy::traffic::TrafficEvent::TrafficEvent()")
    assert element is not None

    element = api_reference.find("asciidoxy::traffic::TrafficEvent::TrafficEvent(TrafficEventData)")
    assert element is not None


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


def test_find_method__select_based_on_args_2__spaces_dont_matter(api_reference):
    with pytest.raises(AmbiguousLookupError):
        api_reference.find("asciidoxy::geometry::Coordinate::Update")

    element = api_reference.find("asciidoxy::geometry::Coordinate::Update( )")
    assert element is None

    element = api_reference.find("asciidoxy::geometry::Coordinate::Update(const Coordinate &)")
    assert element is not None

    element = api_reference.find(
        "asciidoxy::geometry::Coordinate::Update(std::tuple<double,double,double>)")
    assert element is not None

    element = api_reference.find(
        "asciidoxy::geometry::Coordinate::Update( std::tuple<double,double> )")
    assert element is not None

    element = api_reference.find("asciidoxy::geometry::Coordinate::Update(double,double)")
    assert element is not None

    element = api_reference.find("asciidoxy::geometry::Coordinate::Update(double,double,double)")
    assert element is not None


def test_resolve_references_for_return_types(unresolved_api_reference):
    member = unresolved_api_reference.find("asciidoxy::positioning::Positioning::CurrentPosition",
                                           kind="function",
                                           lang="cpp")
    assert member is not None
    assert member.returns
    assert member.returns.type
    assert not member.returns.type.id

    unresolved_api_reference.resolve_references()

    assert member.returns
    assert member.returns.type
    assert member.returns.type.id == "cpp-classasciidoxy_1_1geometry_1_1_coordinate"
    assert member.returns.type.kind == "class"


def test_resolve_partial_references_for_return_types(unresolved_api_reference):
    member = unresolved_api_reference.find("asciidoxy::positioning::Positioning::TrafficNearby",
                                           kind="function",
                                           lang="cpp")
    assert member is not None
    assert member.returns
    assert member.returns.type
    assert len(member.returns.type.nested) == 1
    assert not member.returns.type.nested[0].id

    unresolved_api_reference.resolve_references()

    assert member.returns
    assert member.returns.type
    assert len(member.returns.type.nested) == 1
    assert member.returns.type.nested[0].id == "cpp-classasciidoxy_1_1traffic_1_1_traffic_event"
    assert member.returns.type.nested[0].kind == "class"


def test_resolve_references_for_parameters(unresolved_api_reference):
    member = unresolved_api_reference.find("asciidoxy::positioning::Positioning::IsNearby",
                                           kind="function",
                                           lang="cpp")
    assert member is not None
    assert len(member.params) == 1
    assert member.params[0].type
    assert not member.params[0].type.id

    unresolved_api_reference.resolve_references()

    assert len(member.params) == 1
    assert member.params[0].type
    assert member.params[0].type.id == "cpp-classasciidoxy_1_1geometry_1_1_coordinate"
    assert member.params[0].type.kind == "class"


def test_resolve_partial_references_for_parameters(unresolved_api_reference):
    member = unresolved_api_reference.find("asciidoxy::positioning::Positioning::InTraffic",
                                           kind="function",
                                           lang="cpp")
    assert member is not None
    assert len(member.params) == 1
    assert member.params[0].type
    assert not member.params[0].type.id

    unresolved_api_reference.resolve_references()

    assert len(member.params) == 1
    assert member.params[0].type
    assert member.params[0].type.id == "cpp-classasciidoxy_1_1traffic_1_1_traffic_event"
    assert member.params[0].type.kind == "class"


def test_resolve_references_for_typedefs(unresolved_api_reference):
    member = unresolved_api_reference.find("asciidoxy::positioning::Traffic", kind="alias")
    assert member is not None
    assert member.returns
    assert member.returns.type
    assert not member.returns.type.id

    unresolved_api_reference.resolve_references()

    assert member.returns
    assert member.returns.type
    assert member.returns.type.id == "cpp-classasciidoxy_1_1traffic_1_1_traffic_event"
    assert member.returns.type.kind == "class"


def test_resolve_references_for_inner_type_reference(unresolved_api_reference):
    parent_class = unresolved_api_reference.find("asciidoxy::traffic::TrafficEvent",
                                                 kind="class",
                                                 lang="cpp")
    assert parent_class is not None
    inner_classes = [m for m in parent_class.members if m.kind == "struct"]
    assert len(inner_classes) == 0

    unresolved_api_reference.resolve_references()

    inner_classes = [m for m in parent_class.members if m.kind == "struct"]
    assert len(inner_classes) > 0

    nested_class = inner_classes[0]
    assert nested_class.full_name == "asciidoxy::traffic::TrafficEvent::TrafficEventData"


def test_resolve_references_for_exceptions(unresolved_api_reference):
    member = unresolved_api_reference.find("asciidoxy::positioning::Positioning::Override",
                                           kind="function")
    assert member is not None
    assert len(member.exceptions) == 1
    assert member.exceptions[0].type
    assert not member.exceptions[0].type.id

    unresolved_api_reference.resolve_references()

    assert member.returns
    assert len(member.exceptions) == 1
    assert member.exceptions[0].type
    assert member.exceptions[0].type.id == "cpp-classasciidoxy_1_1geometry_1_1_invalid_coordinate"
    assert member.exceptions[0].type.kind == "class"


def test_resolve_partial_references_for_exceptions(unresolved_api_reference):
    member = unresolved_api_reference.find("asciidoxy::positioning::Positioning::TrafficNearby",
                                           kind="function")
    assert member is not None
    assert len(member.exceptions) == 1
    assert member.exceptions[0].type
    assert not member.exceptions[0].type.id

    unresolved_api_reference.resolve_references()

    assert member.returns
    assert len(member.exceptions) == 1
    assert member.exceptions[0].type
    assert member.exceptions[0].type.id == "cpp-classasciidoxy_1_1geometry_1_1_invalid_coordinate"
    assert member.exceptions[0].type.kind == "class"


def test_resolve_references_prefer_same_namespace(unresolved_api_reference):
    member_a_t = unresolved_api_reference.find("asciidoxy::traffic::CreateConvertor",
                                               kind="function",
                                               lang="cpp")
    assert member_a_t is not None
    assert member_a_t.returns
    assert member_a_t.returns.type
    assert not member_a_t.returns.type.id
    assert not member_a_t.returns.type.kind

    member_a = unresolved_api_reference.find("asciidoxy::CreateConvertor",
                                             kind="function",
                                             lang="cpp")
    assert member_a is not None
    assert member_a.returns
    assert member_a.returns.type
    assert not member_a.returns.type.id
    assert not member_a.returns.type.kind

    member_a_g = unresolved_api_reference.find("asciidoxy::geometry::CreateConvertor",
                                               kind="function",
                                               lang="cpp")
    assert member_a_g is not None
    assert member_a_g.returns
    assert member_a_g.returns.type
    assert not member_a_g.returns.type.id
    assert not member_a_g.returns.type.kind

    unresolved_api_reference.resolve_references()

    assert member_a_t.returns
    assert member_a_t.returns.type
    assert member_a_t.returns.type.id == "cpp-classasciidoxy_1_1traffic_1_1_convertor"
    assert member_a_t.returns.type.kind == "class"
    assert member_a_t.returns.type.namespace == "asciidoxy::traffic"

    assert member_a.returns
    assert member_a.returns.type
    assert member_a.returns.type.id == "cpp-classasciidoxy_1_1_convertor"
    assert member_a.returns.type.kind == "class"
    assert member_a.returns.type.namespace == "asciidoxy"

    assert member_a_g.returns
    assert member_a_g.returns.type
    assert member_a_g.returns.type.id == "cpp-classasciidoxy_1_1geometry_1_1_convertor"
    assert member_a_g.returns.type.kind == "class"
    assert member_a_g.returns.type.namespace == "asciidoxy::geometry"


def test_resolve_references_fails_when_ambiguous(unresolved_api_reference):
    # When internal resolving fails, the type will not be resolved to the exact type, and will be
    # shown in the documentation as plain text. It should not raise an error.
    member = unresolved_api_reference.find("asciidoxy::traffic::geometry::CreateConvertor",
                                           kind="function",
                                           lang="cpp")
    assert member is not None
    assert member.returns
    assert member.returns.type
    assert not member.returns.type.id
    assert not member.returns.type.kind

    unresolved_api_reference.resolve_references()

    assert member.returns
    assert member.returns.type
    assert not member.returns.type.id
    assert not member.returns.type.kind


def test_resolve_references__report_progress(unresolved_api_reference):
    unresolved_ref_count = unresolved_api_reference.unresolved_ref_count
    assert unresolved_ref_count > 70

    progress_mock = ProgressMock()
    unresolved_api_reference.resolve_references(progress=progress_mock)

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == unresolved_ref_count


def test_check_references__reference_found(unresolved_api_reference):
    element = unresolved_api_reference.find("asciidoxy::geometry::Print")
    assert element is not None
    assert len(element.params) == 1
    assert element.params[0].type
    assert element.params[0].type.id

    assert unresolved_api_reference.unchecked_ref_count > 0
    unresolved_api_reference.check_references()
    assert unresolved_api_reference.unchecked_ref_count == 0

    assert element.params[0].type.id


def test_check_references__remove_missing_refids(latest_doxygen_version):
    api_reference = ApiReferenceLoader().version(latest_doxygen_version).add(
        "doxygen", "cpp/default/xml/namespaceasciidoxy_1_1geometry.xml").load()

    element = api_reference.find("asciidoxy::geometry::Print")
    assert element is not None
    assert len(element.params) == 1
    assert element.params[0].type
    assert element.params[0].type.id

    assert api_reference.unchecked_ref_count > 0
    api_reference.check_references()
    assert api_reference.unchecked_ref_count == 0

    assert not element.params[0].type.id


def test_check_references__report_progress(unresolved_api_reference):
    unchecked_ref_count = unresolved_api_reference.unchecked_ref_count
    assert unchecked_ref_count > 0

    progress_mock = ProgressMock()
    unresolved_api_reference.check_references(progress=progress_mock)

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == unchecked_ref_count
