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
"""Test Objective C to Swift transcoding."""

import pytest

from asciidoxy.api_reference import ApiReference
from asciidoxy.model import ReferableElement
from asciidoxy.transcoder.swift import SwiftTranscoder

from .builders import make_member, make_parameter, make_referable, make_return_value, make_type_ref


@pytest.fixture
def transcoder():
    return SwiftTranscoder(ApiReference())


def test_transcode_member__no_arguments(transcoder):
    member = make_member("objc", name="update", namespace="Geo")
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.full_name == "Geo.update"
    assert not transcoded.params


def test_transcode_member__single_argument(transcoder):
    member = make_member("objc",
                         name="updateWithName:",
                         namespace="Geo",
                         params=[make_parameter("name")])
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert len(transcoded.params) == 1
    assert transcoded.params[0].name == "withName"


def test_transcode_member__multiple_arguments(transcoder):
    member = make_member(
        "objc",
        name="updateWithName:andType:andAge:",
        namespace="Geo",
        params=[make_parameter("name"),
                make_parameter("type"),
                make_parameter("age")])
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert len(transcoded.params) == 3
    assert transcoded.params[0].name == "withName"


def test_transcode_member__init(transcoder):
    member = make_member("objc",
                         name="init",
                         namespace="Geo",
                         returns=make_return_value(make_type_ref("objc", "instancetype")))
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.full_name == "Geo.init"
    assert not transcoded.params
    assert not transcoded.returns


def test_transcode_member__init__single_argument(transcoder):
    member = make_member("objc",
                         name="initWithName:",
                         namespace="Geo",
                         params=[make_parameter("name")],
                         returns=make_return_value(make_type_ref("objc", "instancetype")))
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.full_name == "Geo.init"
    assert len(transcoded.params) == 1
    assert transcoded.params[0].name == "name"
    assert not transcoded.returns


def test_transcode_member__init__multiple_arguments(transcoder):
    member = make_member("objc",
                         name="initWithName:andAge",
                         namespace="Geo",
                         params=[make_parameter("nameValue"),
                                 make_parameter("age")],
                         returns=make_return_value(make_type_ref("objc", "instancetype")))
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.full_name == "Geo.init"
    assert len(transcoded.params) == 2
    assert transcoded.params[0].name == "name"
    assert transcoded.params[1].name == "age"
    assert not transcoded.returns


def test_transcode_member__block(transcoder):
    closure = make_member("objc",
                          name="SuccessBlock",
                          namespace="Geo",
                          kind="block",
                          params=[
                              make_parameter("number", type_=make_type_ref("objc", "NSInteger")),
                              make_parameter("data", type_=make_type_ref("objc", "data"))
                          ],
                          returns=make_return_value(make_type_ref("objc", name="BOOL")))
    transcoded = transcoder.member(closure)

    assert transcoded.language == "swift"
    assert transcoded.full_name == "Geo.SuccessBlock"
    assert transcoded.kind == "closure"


def test_transcode_member__only_argument_nserror__no_return(transcoder):
    member = make_member("objc",
                         name="update:",
                         namespace="Geo",
                         kind="function",
                         params=[
                             make_parameter("error",
                                            type_=make_type_ref("objc",
                                                                "NSError",
                                                                prefix="",
                                                                suffix="**"))
                         ])
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert not transcoded.params
    assert len(transcoded.exceptions) == 1
    assert transcoded.exceptions[0].type
    assert transcoded.exceptions[0].type.name == "Error"
    assert not transcoded.exceptions[0].type.prefix
    assert not transcoded.exceptions[0].type.suffix


def test_transcode_member__only_argument_nserror__bool_return(transcoder):
    member = make_member("objc",
                         name="update:",
                         namespace="Geo",
                         kind="function",
                         params=[
                             make_parameter("error",
                                            type_=make_type_ref("objc",
                                                                "NSError",
                                                                prefix="",
                                                                suffix="**"))
                         ],
                         returns=make_return_value(make_type_ref("objc", name="BOOL")))
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert not transcoded.params
    assert len(transcoded.exceptions) == 1
    assert transcoded.exceptions[0].type
    assert transcoded.exceptions[0].type.name == "Error"
    assert not transcoded.exceptions[0].type.prefix
    assert not transcoded.exceptions[0].type.suffix
    assert not transcoded.returns


def test_transcode_member__only_argument_nserror__other_return(transcoder):
    member = make_member("objc",
                         name="update:",
                         namespace="Geo",
                         kind="function",
                         params=[
                             make_parameter("error",
                                            type_=make_type_ref("objc",
                                                                "NSError",
                                                                prefix="",
                                                                suffix="**"))
                         ],
                         returns=make_return_value(make_type_ref("objc", name="NSString")))
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert not transcoded.params
    assert len(transcoded.exceptions) == 1
    assert transcoded.exceptions[0].type
    assert transcoded.exceptions[0].type.name == "Error"
    assert not transcoded.exceptions[0].type.prefix
    assert not transcoded.exceptions[0].type.suffix
    assert transcoded.returns
    assert transcoded.returns.type
    assert transcoded.returns.type.name == "String"


def test_transcode_member__last_argument_nserror__bool_return(transcoder):
    member = make_member("objc",
                         name="update:",
                         namespace="Geo",
                         kind="function",
                         params=[
                             make_parameter("value", type_=make_type_ref("objc", "NSString")),
                             make_parameter("error",
                                            type_=make_type_ref("objc",
                                                                "NSError",
                                                                prefix="",
                                                                suffix="**"))
                         ],
                         returns=make_return_value(make_type_ref("objc", name="BOOL")))
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert len(transcoded.params) == 1
    assert transcoded.params[0].type
    assert transcoded.params[0].type.name == "String"
    assert len(transcoded.exceptions) == 1
    assert transcoded.exceptions[0].type
    assert transcoded.exceptions[0].type.name == "Error"
    assert not transcoded.exceptions[0].type.prefix
    assert not transcoded.exceptions[0].type.suffix
    assert not transcoded.returns


def test_transcode_member__nserror_not_last(transcoder):
    member = make_member("objc",
                         name="update:",
                         namespace="Geo",
                         kind="function",
                         params=[
                             make_parameter("error",
                                            type_=make_type_ref("objc",
                                                                "NSError",
                                                                prefix="",
                                                                suffix="**")),
                             make_parameter("value", type_=make_type_ref("objc", "NSString")),
                         ],
                         returns=make_return_value(make_type_ref("objc", name="BOOL")))
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert len(transcoded.params) == 2
    assert not transcoded.exceptions
    assert transcoded.returns


def test_transcode_member__only_argument_nserror__with_error(transcoder):
    member = make_member("objc",
                         name="updateWithError:",
                         namespace="Geo",
                         kind="function",
                         params=[
                             make_parameter("error",
                                            type_=make_type_ref("objc",
                                                                "NSError",
                                                                prefix="",
                                                                suffix="**"))
                         ])
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert not transcoded.params
    assert len(transcoded.exceptions) == 1
    assert transcoded.exceptions[0].type
    assert transcoded.exceptions[0].type.name == "Error"
    assert not transcoded.exceptions[0].type.prefix
    assert not transcoded.exceptions[0].type.suffix


def test_transcode_member__only_argument_nserror__and_return_error(transcoder):
    member = make_member("objc",
                         name="updateAndReturnError:",
                         namespace="Geo",
                         kind="function",
                         params=[
                             make_parameter("error",
                                            type_=make_type_ref("objc",
                                                                "NSError",
                                                                prefix="",
                                                                suffix="**"))
                         ])
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert not transcoded.params
    assert len(transcoded.exceptions) == 1
    assert transcoded.exceptions[0].type
    assert transcoded.exceptions[0].type.name == "Error"
    assert not transcoded.exceptions[0].type.prefix
    assert not transcoded.exceptions[0].type.suffix


def test_transcode_member__return_optional_removed(transcoder):
    member = make_member("objc",
                         name="updateAndReturnError:",
                         namespace="Geo",
                         kind="function",
                         params=[
                             make_parameter("error",
                                            type_=make_type_ref("objc",
                                                                "NSError",
                                                                prefix="",
                                                                suffix="**")),
                         ],
                         returns=make_return_value(
                             make_type_ref("objc", name="NSString", prefix="", suffix="?")))
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert not transcoded.params
    assert len(transcoded.exceptions) == 1
    assert transcoded.exceptions[0].type
    assert transcoded.exceptions[0].type.name == "Error"
    assert not transcoded.exceptions[0].type.prefix
    assert not transcoded.exceptions[0].type.suffix
    assert transcoded.returns
    assert transcoded.returns.type
    assert transcoded.returns.type.name == "String"
    assert not transcoded.returns.type.suffix


def test_transcode_member__nserror_followed_by_closure(transcoder):
    member = make_member("objc",
                         name="update:",
                         namespace="Geo",
                         kind="function",
                         params=[
                             make_parameter("error",
                                            type_=make_type_ref("objc",
                                                                "NSError",
                                                                prefix="",
                                                                suffix="**")),
                             make_parameter("callback",
                                            type_=make_type_ref("objc", "", prefix="", suffix=""))
                         ])
    member.params[1].type.args = [make_parameter("value")]
    member.params[1].returns = make_type_ref("objc", "void", prefix="", suffix="")
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert len(transcoded.params) == 1
    assert transcoded.params[0].name == "callback"
    assert len(transcoded.exceptions) == 1
    assert transcoded.exceptions[0].type
    assert transcoded.exceptions[0].type.name == "Error"
    assert not transcoded.exceptions[0].type.prefix
    assert not transcoded.exceptions[0].type.suffix


def test_transcode_member__only_argument_nserror__swift_nothrow(transcoder):
    member = make_member("objc",
                         name="update:",
                         namespace="Geo",
                         kind="function",
                         params=[
                             make_parameter("error",
                                            type_=make_type_ref("objc",
                                                                "NSError",
                                                                prefix="",
                                                                suffix="**"))
                         ],
                         returns=make_return_value(make_type_ref("objc", name="BOOL")))
    member.args = "([error] NSError ** NS_SWIFT_NOTHROW)"
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert len(transcoded.params) == 1
    assert not transcoded.exceptions
    assert transcoded.returns


def test_transcode_member__void_return(transcoder):
    member = make_member("objc",
                         name="update",
                         namespace="Geo",
                         kind="function",
                         returns=make_return_value(make_type_ref("objc", name="void")))
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.full_name == "Geo.update"
    assert transcoded.returns is None


@pytest.mark.parametrize("objc_name, swift_name", [
    ("NSObject", "NSObject"),
    ("NSAutoReleasePool", "NSAutoReleasePool"),
    ("NSException", "NSException"),
    ("NSProxy", "NSProxy"),
    ("NSBackgroundActivity", "NSBackgroundActivity"),
    ("NSUserNotification", "NSUserNotification"),
    ("NSXPCConnection", "NSXPCConnection"),
    ("NSNumber", "NSNumber"),
    ("NSDecimalNumber", "Decimal"),
    ("NSArray", "Array"),
    ("NSDate", "Date"),
    ("NSURL", "URL"),
    ("NSURLRequest", "URLRequest"),
    ("NSUUID", "UUID"),
    ("init:", "init"),
    ("initWithName:", "initWithName"),
    ("initWithName:andAge:", "initWithName"),
    ("BOOL", "Bool"),
])
def test_convert_name(transcoder, objc_name, swift_name):
    element = make_referable(ReferableElement, lang="objc", name=objc_name)
    assert transcoder.convert_name(element) == swift_name


@pytest.mark.parametrize("objc_name, objc_full_name, swift_full_name", [
    ("NSObject", "NSObject", "NSObject"),
    ("NSURL", "URL", "URL"),
    ("NSUUID", "UUID", "UUID"),
    ("init:", "MyClass.init:", "MyClass.init"),
    ("initWithName:", "MyClass.initWithName:", "MyClass.initWithName"),
    ("initWithName:andAge:", "MyClass.initWithName:andAge:", "MyClass.initWithName"),
])
def test_convert_full_name(transcoder, objc_name, objc_full_name, swift_full_name):
    element = make_referable(ReferableElement, lang="objc", name=objc_name)
    element.full_name = objc_full_name
    assert transcoder.convert_full_name(element) == swift_full_name


def test_transcode_type_ref__nullable_prefix(transcoder):
    type_ref = make_type_ref(lang="objc", name="MyClass", prefix="nullable ", suffix="")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == "MyClass"
    assert not transcoded.prefix
    assert transcoded.suffix == "?"


def test_transcode_type_ref__nullable_suffix(transcoder):
    type_ref = make_type_ref(lang="objc", name="MyClass", prefix="", suffix=" _Nullable")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == "MyClass"
    assert not transcoded.prefix
    assert transcoded.suffix == "?"


def test_transcode_type_ref__pointer(transcoder):
    type_ref = make_type_ref(lang="objc", name="MyClass", prefix="", suffix=" *")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == "MyClass"
    assert not transcoded.prefix
    assert not transcoded.suffix


def test_transcode_type_ref__autoreleasing(transcoder):
    type_ref = make_type_ref(lang="objc", name="MyClass", prefix="", suffix="*__autoreleasing")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == "MyClass"
    assert not transcoded.prefix
    assert not transcoded.suffix


def test_transcode_type_ref__bare_id(transcoder):
    type_ref = make_type_ref(lang="objc", name="id", prefix="", suffix="")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == "Any"
    assert not transcoded.prefix
    assert not transcoded.suffix


def test_transcode_type_ref__id_type(transcoder):
    type_ref = make_type_ref(lang="objc", name="id", prefix="", suffix="")
    type_ref.nested = [make_type_ref(lang="objc", name="MyClass", prefix="", suffix="")]
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == "MyClass"
    assert not transcoded.prefix
    assert not transcoded.suffix
    assert not transcoded.nested


def test_transcode_type_ref__closure(transcoder):
    type_ref = make_type_ref("objc", name="", prefix="", suffix="")
    type_ref.returns = make_type_ref("objc", "Coordinate", prefix="", suffix="")
    type_ref.args = [
        make_parameter("arg1"),
        make_parameter("arg2", make_type_ref("objc", "MyType", prefix="", suffix="")),
    ]

    transcoded = transcoder.type_ref(type_ref)

    assert transcoded is not type_ref
    assert transcoded.language == "swift"
    assert not transcoded.name
    assert not transcoded.nested
    assert len(transcoded.args) == 2
    assert transcoded.returns is not None
    assert not transcoded.prefix
    assert not transcoded.suffix


def test_transcode_type_ref__nullable_closure(transcoder):
    type_ref = make_type_ref("objc", name="", prefix="", suffix="")
    type_ref.returns = make_type_ref("objc", "Coordinate", prefix="nullable ", suffix="")
    type_ref.args = [
        make_parameter("arg1"),
        make_parameter("arg2", make_type_ref("objc", "MyType", prefix="", suffix="")),
    ]

    transcoded = transcoder.type_ref(type_ref)

    assert transcoded is not type_ref
    assert transcoded.language == "swift"
    assert not transcoded.name
    assert not transcoded.nested
    assert len(transcoded.args) == 2

    assert transcoded.returns is not None
    assert not transcoded.prefix
    assert transcoded.suffix == "?"
    assert not transcoded.returns.prefix
    assert not transcoded.returns.suffix
