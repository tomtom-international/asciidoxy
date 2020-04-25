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
"""Tests for API reference storage and search."""

from asciidoxy.api_reference import NameFilter, ParameterTypeMatcher


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
