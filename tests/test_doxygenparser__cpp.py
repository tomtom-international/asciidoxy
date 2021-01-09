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
"""Tests for parsing C++ from Doxygen XML files."""

import pytest


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_class(api_reference):
    cpp_class = api_reference.find("asciidoxy::geometry::Coordinate", kind="class", lang="cpp")
    assert cpp_class is not None
    assert cpp_class.id == "cpp-classasciidoxy_1_1geometry_1_1_coordinate"
    assert cpp_class.name == "Coordinate"
    assert cpp_class.full_name == "asciidoxy::geometry::Coordinate"
    assert cpp_class.language == "cpp"
    assert cpp_class.kind == "class"
    assert cpp_class.brief == "Class to hold information about a coordinate."
    assert cpp_class.description == "A coordinate has a latitude, longitude, and an altitude."
    assert cpp_class.include == "coordinate.hpp"
    assert cpp_class.namespace == "asciidoxy::geometry"

    assert len(cpp_class.members) == 15
    assert len(cpp_class.enumvalues) == 0

    member_names = sorted(m.name for m in cpp_class.members)
    assert member_names == sorted([
        "Coordinate",
        "~Coordinate",
        "operator+",
        "Latitude",
        "Longitude",
        "Altitude",
        "IsValid",
        "latitude_",
        "longitude_",
        "altitude_",
        "Update",
        "Update",
        "Update",
        "Update",
        "Update",
    ])


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_class_with_nested_class(api_reference):
    cpp_class = api_reference.find("asciidoxy::traffic::TrafficEvent", kind="class", lang="cpp")
    assert cpp_class is not None
    assert cpp_class.id == "cpp-classasciidoxy_1_1traffic_1_1_traffic_event"
    assert cpp_class.namespace == "asciidoxy::traffic"
    assert len(cpp_class.inner_classes) == 1

    nested_class = cpp_class.inner_classes[0]
    assert nested_class.name == "asciidoxy::traffic::TrafficEvent::TrafficEventData"
    assert nested_class.namespace == "asciidoxy::traffic::TrafficEvent"
    assert nested_class.id == ("cpp-structasciidoxy_1_1traffic_1_1_traffic_event_1_1_traffic_"
                               "event_data")
    assert nested_class.language == "cpp"
    assert nested_class.prot == "public"

    assert nested_class.referred_object is not None
    assert nested_class.referred_object.id == nested_class.id


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_class__ignore_friend_declarations(api_reference):
    cpp_class = api_reference.find("asciidoxy::system::ServiceStarter", kind="class", lang="cpp")
    assert cpp_class is not None
    assert len([member for member in cpp_class.members if member.kind == "friend"]) == 0


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_member_function_no_return_value(api_reference):
    member = api_reference.find("asciidoxy::geometry::Coordinate::Coordinate",
                                kind="function",
                                lang="cpp")
    assert member is not None
    assert member.id == ("cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                         "1a69ac21cad618c0c033815f2cbdc86318")
    assert member.name == "Coordinate"
    assert member.full_name == "asciidoxy::geometry::Coordinate::Coordinate"
    assert member.language == "cpp"
    assert member.kind == "function"
    assert member.definition == "asciidoxy::geometry::Coordinate::Coordinate"
    assert member.args == "()"
    assert member.brief == "Default constructor."
    assert member.description == ""
    assert member.prot == "public"
    assert member.static is False
    assert member.include == "coordinate.hpp"
    assert member.namespace == "asciidoxy::geometry::Coordinate"
    assert member.const is False

    assert len(member.params) == 0
    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0
    assert member.returns is None


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_member_function_only_return_value(api_reference):
    member = api_reference.find("asciidoxy::geometry::Coordinate::IsValid",
                                kind="function",
                                lang="cpp")
    assert member is not None
    assert member.id == ("cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                         "1a8d7e0eac29549fa4666093e36914deac")
    assert member.name == "IsValid"
    assert member.full_name == "asciidoxy::geometry::Coordinate::IsValid"
    assert member.language == "cpp"
    assert member.kind == "function"
    assert member.definition == "bool asciidoxy::geometry::Coordinate::IsValid"
    assert member.args == "() const"
    assert member.brief == "Check if the coordinate is valid."
    assert member.description == "A coordinate is valid if its values are within WGS84 bounds."
    assert member.prot == "public"
    assert member.static is False
    assert member.include == "coordinate.hpp"
    assert member.namespace == "asciidoxy::geometry::Coordinate"
    assert member.const is True

    assert len(member.params) == 0
    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0

    assert member.returns is not None
    assert member.returns.description == "True if valid, false if not."
    assert member.returns.type is not None
    assert member.returns.type.id is None
    assert member.returns.type.kind is None
    assert member.returns.type.language == "cpp"
    assert member.returns.type.name == "bool"
    assert not member.returns.type.prefix
    assert not member.returns.type.suffix
    assert not member.returns.type.nested
    assert member.returns.type.namespace == "asciidoxy::geometry::Coordinate"


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_member_function_params_and_return_value(api_reference):
    member = api_reference.find("asciidoxy::traffic::TrafficEvent::Update",
                                kind="function",
                                lang="cpp")
    assert member is not None
    assert member.id == ("cpp-classasciidoxy_1_1traffic_1_1_traffic_event_"
                         "1a829eda83200a17d2d2f8a5fced5f000b")
    assert member.name == "Update"
    assert member.full_name == "asciidoxy::traffic::TrafficEvent::Update"
    assert member.language == "cpp"
    assert member.kind == "function"
    assert member.definition == "bool asciidoxy::traffic::TrafficEvent::Update"
    assert member.args == "(int cause, int delay)"
    assert member.brief == "Update the traffic event data."
    assert member.description == "Verifies the new information before updating."
    assert member.prot == "public"
    assert member.static is False
    assert member.include == "traffic_event.hpp"
    assert member.namespace == "asciidoxy::traffic::TrafficEvent"
    assert member.const is False

    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0

    assert len(member.params) == 2
    param1, param2 = member.params

    assert param1.name == "cause"
    assert param1.description == "New TPEG cause code."
    assert not param1.default_value

    assert param1.type is not None
    assert param1.type.id is None
    assert param1.type.kind is None
    assert param1.type.language == "cpp"
    assert param1.type.name == "int"
    assert param1.type.namespace == "asciidoxy::traffic::TrafficEvent"

    assert not param1.type.prefix
    assert not param1.type.suffix
    assert not param1.type.nested

    assert param2.name == "delay"
    assert param2.description == "New delay in seconds."
    assert not param2.default_value

    assert param2.type is not None
    assert param2.type.id is None
    assert param2.type.kind is None
    assert param2.type.language == "cpp"
    assert param2.type.name == "int"
    assert param2.type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert not param2.type.prefix
    assert not param2.type.suffix
    assert not param2.type.nested

    assert member.returns is not None
    assert member.returns.description == "True if the update is valid."
    assert member.returns.type is not None
    assert member.returns.type.id is None
    assert member.returns.type.kind is None
    assert member.returns.type.language == "cpp"
    assert member.returns.type.name == "bool"
    assert member.returns.type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert not member.returns.type.prefix
    assert not member.returns.type.suffix
    assert not member.returns.type.nested


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_member_function_with_nested_return_type(api_reference):
    member = api_reference.find("asciidoxy::traffic::TrafficEvent::SharedData",
                                kind="function",
                                lang="cpp")
    assert member is not None
    assert member.name == "SharedData"
    assert member.namespace == "asciidoxy::traffic::TrafficEvent"

    assert member.returns is not None
    assert member.returns.description == "The shared pointer."
    assert member.returns.type is not None
    assert member.returns.type.id is None
    assert member.returns.type.kind is None
    assert member.returns.type.language == "cpp"
    assert member.returns.type.name == "std::shared_ptr"
    assert member.include == "traffic_event.hpp"
    assert member.returns.type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert not member.returns.type.prefix
    assert not member.returns.type.suffix

    assert len(member.returns.type.nested) == 1
    nested_type = member.returns.type.nested[0]
    assert nested_type.id == ("cpp-structasciidoxy_1_1traffic_1_1_traffic_event_1_1"
                              "_traffic_event_data")
    assert nested_type.kind == "compound"
    assert nested_type.language == "cpp"
    assert nested_type.name == "TrafficEventData"
    assert nested_type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert not nested_type.prefix
    assert not nested_type.suffix
    assert not nested_type.nested


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_member_enum(api_reference):
    member = api_reference.find("asciidoxy::traffic::TrafficEvent::Severity",
                                kind="enum",
                                lang="cpp")
    assert member is not None
    assert member.name == "Severity"
    assert member.brief == "Severity scale for traffic events."
    assert (member.description ==
            "The more severe the traffic event, the more likely it is to have a large delay.")
    assert member.include == "traffic_event.hpp"

    assert len(member.enumvalues) == 4
    enum_value = [e for e in member.enumvalues if e.name == "High"][0]
    assert enum_value.id == ("cpp-classasciidoxy_1_1traffic_1_1_traffic_event_"
                             "1a47c51b1f1f014cb943377fb67ad903b9a655d20c1ca69519ca647684edbb2db35")
    assert enum_value.name == "High"
    assert enum_value.full_name == "asciidoxy::traffic::TrafficEvent::Severity::High"
    assert enum_value.language == "cpp"
    assert enum_value.initializer == "= 3"
    assert enum_value.brief == "High severity."
    assert enum_value.description == "Better stay away here."
    assert enum_value.kind == "enumvalue"


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_member_function_with_exception(api_reference):
    member = api_reference.find("asciidoxy::traffic::TrafficEvent::CalculateDelay()",
                                kind="function",
                                lang="cpp")
    assert member is not None
    assert member.name == "CalculateDelay"
    assert member.namespace == "asciidoxy::traffic::TrafficEvent"
    assert member.include == "traffic_event.hpp"

    assert len(member.exceptions) == 1
    assert member.exceptions[0].type
    assert member.exceptions[0].type.name == "std::runtime_exception"
    assert member.exceptions[0].type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert member.exceptions[0].description == "Thrown when the update encounters a critical error."


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_member_function_with_std_function_argument(api_reference):
    member = api_reference.find("asciidoxy::traffic::TrafficEvent::RegisterTrafficCallback",
                                kind="function",
                                lang="cpp")
    assert member is not None
    assert member.name == "RegisterTrafficCallback"
    assert member.namespace == "asciidoxy::traffic::TrafficEvent"
    assert member.include == "traffic_event.hpp"
    assert len(member.params) == 1

    param = member.params[0]
    assert param.type
    assert param.name == "callback"
    assert param.description == "A function to call on updates."

    assert not param.type.id
    assert not param.type.prefix
    assert param.type.name == "std::function"
    assert not param.type.suffix
    assert param.type.language == "cpp"
    assert param.type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert len(param.type.nested) == 1
    assert not param.type.args

    nested = param.type.nested[0]
    assert nested.kind == "closure"
    assert not nested.id
    assert not nested.prefix
    assert not nested.name
    assert not nested.suffix
    assert not nested.nested
    assert len(nested.args) == 2

    assert nested.returns is not None
    assert not nested.returns.id
    assert not nested.returns.prefix
    assert nested.returns.name == "void"
    assert not nested.returns.suffix
    assert not nested.returns.nested
    assert not nested.returns.args
    assert not nested.returns.nested

    arg_1 = nested.args[0]
    assert not arg_1.name
    assert arg_1.type
    assert (
        arg_1.type.id == "cpp-structasciidoxy_1_1traffic_1_1_traffic_event_1_1_traffic_event_data")
    assert arg_1.type.prefix == "const "
    assert arg_1.type.name == "TrafficEventData"
    assert arg_1.type.suffix == " &"
    assert not arg_1.type.nested
    assert not arg_1.type.args

    arg_2 = nested.args[1]
    assert arg_2.name == "delay"
    assert arg_2.type
    assert not arg_2.type.id
    assert not arg_2.type.prefix
    assert arg_2.type.name == "int"
    assert not arg_2.type.suffix
    assert not arg_2.type.nested
    assert not arg_2.type.args


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_member_function_with_complex_std_function_argument(api_reference):
    member = api_reference.find(
        "asciidoxy::relative_namespace::InterfaceWithDetailClasses::DoSomething",
        kind="function",
        lang="cpp")
    assert member is not None
    assert len(member.params) == 3

    param = member.params[0]
    assert param.name == "text"
    assert param.type

    param = member.params[1]
    assert param.name == "success_callback"
    assert param.type
    assert param.type.name == "std::function"
    assert len(param.type.nested) == 1
    assert param.type.args is None

    nested = param.type.nested[0]
    assert not nested.name
    assert nested.returns
    assert nested.returns.name == "void"
    assert len(nested.args) == 1

    arg = nested.args[0]
    assert not arg.name
    assert arg.type
    assert arg.type.name == "std::shared_ptr"
    assert arg.type.prefix == "const "
    assert arg.type.suffix == " &"
    assert arg.type.args is None
    assert len(arg.type.nested) == 1

    nested_again = arg.type.nested[0]
    assert nested_again.name == "detail::SuccessDescriptor"
    assert nested_again.id
    assert nested_again.args is None
    assert nested_again.nested is None

    param = member.params[2]
    assert param.name == "error_callback"
    assert param.type
    assert param.type.name == "std::function"
    assert len(param.type.nested) == 1
    assert param.type.args is None

    nested = param.type.nested[0]
    assert not nested.name
    assert nested.returns
    assert nested.returns.name == "void"
    assert len(nested.args) == 1

    arg = nested.args[0]
    assert not arg.name
    assert arg.type
    assert arg.type.name == "detail::ErrorDescriptor"
    assert arg.type.args is None
    assert arg.type.nested is None


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_member_function__deleted(api_reference):
    member = api_reference.find("asciidoxy::system::MoveOnly::MoveOnly(const MoveOnly&)",
                                kind="function",
                                lang="cpp")
    assert member is not None
    assert member.deleted is True
    assert member.default is False


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp_member_function__default(api_reference):
    member = api_reference.find("asciidoxy::system::MoveOnly::operator=(MoveOnly&&)",
                                kind="function",
                                lang="cpp")
    assert member is not None
    assert member.deleted is False
    assert member.default is True


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp__include_file_for_free_functions(api_reference):
    function = api_reference.find("asciidoxy::system::CreateService", kind="function", lang="cpp")
    assert function is not None
    assert function.include == "service.hpp"


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp__default_parameter_values__constructor(api_reference):
    member = api_reference.find("asciidoxy::geometry::Point::Point", kind="function", lang="cpp")
    assert member is not None
    assert len(member.params) == 2

    param1 = member.params[0]
    assert param1.name == "x"
    assert param1.default_value == "0"

    param2 = member.params[1]
    assert param2.name == "y"
    assert param2.default_value == "1"


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp__default_parameter_values__method(api_reference):
    member = api_reference.find("asciidoxy::geometry::Point::increment",
                                kind="function",
                                lang="cpp")
    assert member is not None
    assert len(member.params) == 2

    param1 = member.params[0]
    assert param1.name == "x"
    assert param1.default_value == "2"

    param2 = member.params[1]
    assert param2.name == "y"
    assert param2.default_value == "3"


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]])
def test_parse_cpp__constexpr_constructor(api_reference):
    member = api_reference.find("ConstInt::ConstInt", kind="function", lang="cpp")
    assert member is not None
    assert len(member.params) == 1

    assert member.returns is None
    assert member.constexpr is True
