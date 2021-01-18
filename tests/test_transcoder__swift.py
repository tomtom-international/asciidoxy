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
from asciidoxy.transcoder.swift import SwiftTranscoder

from .builders import (make_compound, make_parameter, make_return_value, make_throws_clause,
                       make_type_ref)


def make_objc_compound(**kwargs):
    return make_compound(language="objc", **kwargs)


def make_swift_compound(**kwargs):
    return make_compound(language="swift", **kwargs)


def make_objc_type_ref(**kwargs):
    return make_type_ref(language="objc", **kwargs)


def make_swift_type_ref(**kwargs):
    return make_type_ref(language="swift", **kwargs)


def make_swift_throws_clause(**kwargs):
    return make_throws_clause(language="swift", **kwargs)


@pytest.fixture
def transcoder():
    return SwiftTranscoder(ApiReference())


def test_transcode_function__no_arguments(transcoder):
    compound = make_objc_compound(name="update",
                                  namespace="Geo",
                                  full_name="Geo.update",
                                  kind="function")
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(name="update",
                                             namespace="Geo",
                                             full_name="Geo.update",
                                             kind="function")


def test_transcode_function__single_argument(transcoder):
    compound = make_objc_compound(name="updateWithName:",
                                  namespace="Geo",
                                  full_name="Geo.updateWithName:",
                                  params=[make_parameter(name="name")],
                                  kind="function")
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(id="swift-updatewithname:",
                                             name="update",
                                             namespace="Geo",
                                             full_name="Geo.update",
                                             params=[make_parameter(name="withName")],
                                             kind="function")

    assert transcoded.language == "swift"
    assert transcoded.name == "update"
    assert transcoded.full_name == "Geo.update"
    assert len(transcoded.params) == 1
    assert transcoded.params[0].name == "withName"


def test_transcode_compound__multiple_arguments(transcoder):
    compound = make_objc_compound(name="updateWithName:andType:andAge:",
                                  namespace="Geo",
                                  kind="function",
                                  params=[
                                      make_parameter(name="name"),
                                      make_parameter(name="type"),
                                      make_parameter(name="age")
                                  ])
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(id="swift-updatewithname:andtype:andage:",
                                             name="update",
                                             namespace="Geo",
                                             kind="function",
                                             params=[
                                                 make_parameter(name="withName"),
                                                 make_parameter(name="type"),
                                                 make_parameter(name="age")
                                             ])


def test_transcode_compound__init(transcoder):
    compound = make_objc_compound(
        name="init",
        namespace="Geo",
        kind="function",
        returns=make_return_value(type=make_objc_type_ref(name="instancetype")))
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(name="init",
                                             namespace="Geo",
                                             kind="function",
                                             returns=None)


def test_transcode_compound__init__single_argument(transcoder):
    compound = make_objc_compound(
        name="initWithName:",
        namespace="Geo",
        kind="function",
        params=[make_parameter(name="name")],
        returns=make_return_value(type=make_objc_type_ref(name="instancetype")))
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(id="swift-initwithname:",
                                             name="init",
                                             namespace="Geo",
                                             kind="function",
                                             params=[make_parameter(name="name")],
                                             returns=None)


def test_transcode_compound__init__multiple_arguments(transcoder):
    compound = make_objc_compound(
        name="initWithName:andAge:",
        namespace="Geo",
        kind="function",
        params=[make_parameter(name="nameValue"),
                make_parameter(name="age")],
        returns=make_return_value(type=make_objc_type_ref(name="instancetype")))
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-initwithname:andage:",
        name="init",
        namespace="Geo",
        kind="function",
        params=[make_parameter(name="name"),
                make_parameter(name="age")],
        returns=None)


def test_transcode_compound__block(transcoder):
    closure = make_objc_compound(name="SuccessBlock",
                                 namespace="Geo",
                                 kind="block",
                                 params=[
                                     make_parameter(name="number",
                                                    type=make_objc_type_ref(name="NSInteger")),
                                     make_parameter(name="data",
                                                    type=make_objc_type_ref(name="data"))
                                 ],
                                 returns=make_return_value(type=make_objc_type_ref(name="BOOL")))
    transcoded = transcoder.compound(closure)
    assert transcoded == make_swift_compound(
        name="SuccessBlock",
        namespace="Geo",
        kind="closure",
        params=[
            make_parameter(name="number",
                           type=make_swift_type_ref(name="Integer", id="swift-nsinteger")),
            make_parameter(name="data", type=make_swift_type_ref(name="data"))
        ],
        returns=make_return_value(type=make_swift_type_ref(name="Bool")))


def test_transcode_compound__only_argument_nserror__no_return(transcoder):
    compound = make_objc_compound(name="update:",
                                  namespace="Geo",
                                  kind="function",
                                  params=[
                                      make_parameter(name="error",
                                                     type=make_objc_type_ref(name="NSError",
                                                                             prefix="",
                                                                             suffix="**"))
                                  ])
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-update:",
        name="update",
        namespace="Geo",
        kind="function",
        params=[],
        exceptions=[
            make_swift_throws_clause(
                type=make_swift_type_ref(name="Error", id="swift-nserror", prefix="", suffix=""))
        ])


def test_transcode_compound__only_argument_nserror__bool_return(transcoder):
    compound = make_objc_compound(name="update:",
                                  namespace="Geo",
                                  kind="function",
                                  params=[
                                      make_parameter(name="error",
                                                     type=make_objc_type_ref(name="NSError",
                                                                             prefix="",
                                                                             suffix="**"))
                                  ],
                                  returns=make_return_value(type=make_objc_type_ref(name="BOOL")))
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-update:",
        name="update",
        namespace="Geo",
        kind="function",
        params=[],
        returns=None,
        exceptions=[
            make_swift_throws_clause(
                type=make_swift_type_ref(name="Error", id="swift-nserror", prefix="", suffix=""))
        ])


def test_transcode_compound__only_argument_nserror__other_return(transcoder):
    compound = make_objc_compound(
        name="update:",
        namespace="Geo",
        kind="function",
        params=[
            make_parameter(name="error",
                           type=make_objc_type_ref(name="NSError", prefix="", suffix="**"))
        ],
        returns=make_return_value(type=make_objc_type_ref(name="NSString")))
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-update:",
        name="update",
        namespace="Geo",
        kind="function",
        params=[],
        exceptions=[
            make_swift_throws_clause(
                type=make_swift_type_ref(name="Error", id="swift-nserror", prefix="", suffix=""))
        ],
        returns=make_return_value(type=make_swift_type_ref(name="String", id="swift-nsstring")))


def test_transcode_compound__last_argument_nserror__bool_return(transcoder):
    compound = make_objc_compound(name="update:",
                                  namespace="Geo",
                                  kind="function",
                                  params=[
                                      make_parameter(name="value",
                                                     type=make_objc_type_ref(name="NSString")),
                                      make_parameter(name="error",
                                                     type=make_objc_type_ref(name="NSError",
                                                                             prefix="",
                                                                             suffix="**"))
                                  ],
                                  returns=make_return_value(type=make_objc_type_ref(name="BOOL")))
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-update:",
        name="update",
        namespace="Geo",
        kind="function",
        params=[
            make_parameter(name="value",
                           type=make_swift_type_ref(name="String", id="swift-nsstring")),
        ],
        returns=None,
        exceptions=[
            make_swift_throws_clause(
                type=make_swift_type_ref(name="Error", id="swift-nserror", prefix="", suffix=""))
        ],
    )


def test_transcode_compound__nserror_not_last(transcoder):
    compound = make_objc_compound(name="update:",
                                  namespace="Geo",
                                  kind="function",
                                  params=[
                                      make_parameter(name="error",
                                                     type=make_objc_type_ref(name="NSError",
                                                                             prefix="",
                                                                             suffix="**")),
                                      make_parameter(name="value",
                                                     type=make_objc_type_ref(name="NSString")),
                                  ],
                                  returns=make_return_value(type=make_objc_type_ref(name="BOOL")))
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-update:",
        name="update",
        namespace="Geo",
        kind="function",
        params=[
            make_parameter(name="error",
                           type=make_swift_type_ref(id="swift-nserror",
                                                    name="Error",
                                                    prefix="",
                                                    suffix="")),
            make_parameter(name="value",
                           type=make_swift_type_ref(id="swift-nsstring", name="String")),
        ],
        returns=make_return_value(type=make_swift_type_ref(name="Bool")))


def test_transcode_compound__only_argument_nserror__with_error(transcoder):
    compound = make_objc_compound(name="updateWithError:",
                                  namespace="Geo",
                                  kind="function",
                                  params=[
                                      make_parameter(name="error",
                                                     type=make_objc_type_ref(name="NSError",
                                                                             prefix="",
                                                                             suffix="**"))
                                  ])
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-updatewitherror:",
        name="update",
        namespace="Geo",
        kind="function",
        params=[],
        exceptions=[
            make_swift_throws_clause(
                type=make_swift_type_ref(name="Error", id="swift-nserror", prefix="", suffix=""))
        ])


def test_transcode_compound__only_argument_nserror__and_return_error(transcoder):
    compound = make_objc_compound(name="updateAndReturnError:",
                                  namespace="Geo",
                                  kind="function",
                                  params=[
                                      make_parameter(name="error",
                                                     type=make_objc_type_ref(name="NSError",
                                                                             prefix="",
                                                                             suffix="**"))
                                  ])
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-updateandreturnerror:",
        name="update",
        namespace="Geo",
        kind="function",
        params=[],
        exceptions=[
            make_swift_throws_clause(
                type=make_swift_type_ref(name="Error", id="swift-nserror", prefix="", suffix=""))
        ])


def test_transcode_compound__return_optional_removed(transcoder):
    compound = make_objc_compound(
        name="updateAndReturnError:",
        namespace="Geo",
        kind="function",
        params=[
            make_parameter(name="error",
                           type=make_objc_type_ref(name="NSError", prefix="", suffix="**")),
        ],
        returns=make_return_value(type=make_objc_type_ref(name="NSString", prefix="", suffix="?")))
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-updateandreturnerror:",
        name="update",
        namespace="Geo",
        kind="function",
        params=[],
        returns=make_return_value(
            type=make_swift_type_ref(id="swift-nsstring", name="String", prefix="", suffix="")),
        exceptions=[
            make_swift_throws_clause(
                type=make_swift_type_ref(name="Error", id="swift-nserror", prefix="", suffix=""))
        ])


def test_transcode_compound__nserror_followed_by_closure(transcoder):
    compound = make_objc_compound(name="update:",
                                  namespace="Geo",
                                  kind="function",
                                  params=[
                                      make_parameter(name="error",
                                                     type=make_objc_type_ref(name="NSError",
                                                                             prefix="",
                                                                             suffix="**")),
                                      make_parameter(name="callback",
                                                     type=make_objc_type_ref(
                                                         name="",
                                                         prefix="",
                                                         suffix="",
                                                         args=[make_parameter(name="value")],
                                                         returns=make_objc_type_ref(name="void",
                                                                                    prefix="",
                                                                                    suffix="")))
                                  ])
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-update:",
        name="update",
        namespace="Geo",
        kind="function",
        params=[
            make_parameter(name="callback",
                           type=make_swift_type_ref(name="",
                                                    prefix="",
                                                    suffix="",
                                                    args=[make_parameter(name="value")],
                                                    returns=make_swift_type_ref(name="void",
                                                                                prefix="",
                                                                                suffix="")))
        ],
        exceptions=[
            make_swift_throws_clause(
                type=make_swift_type_ref(name="Error", id="swift-nserror", prefix="", suffix=""))
        ])


def test_transcode_compound__only_argument_nserror__swift_nothrow(transcoder):
    compound = make_objc_compound(name="update:",
                                  namespace="Geo",
                                  kind="function",
                                  params=[
                                      make_parameter(name="error",
                                                     type=make_objc_type_ref(name="NSError",
                                                                             prefix="",
                                                                             suffix="**"))
                                  ],
                                  returns=make_return_value(type=make_objc_type_ref(name="BOOL")),
                                  args="([error] NSError ** NS_SWIFT_NOTHROW)")
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(
        id="swift-update:",
        name="update",
        namespace="Geo",
        kind="function",
        params=[
            make_parameter(name="error",
                           type=make_swift_type_ref(id="swift-nserror",
                                                    name="Error",
                                                    prefix="",
                                                    suffix=""))
        ],
        returns=make_return_value(type=make_swift_type_ref(name="Bool")),
        args="([error] NSError ** NS_SWIFT_NOTHROW)")


def test_transcode_compound__void_return(transcoder):
    compound = make_objc_compound(name="update",
                                  namespace="Geo",
                                  kind="function",
                                  returns=make_return_value(type=make_objc_type_ref(name="void")))
    transcoded = transcoder.compound(compound)
    assert transcoded == make_swift_compound(name="update",
                                             namespace="Geo",
                                             kind="function",
                                             returns=None)


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
    element = make_objc_compound(name=objc_name)
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
    element = make_objc_compound(name=objc_name)
    element.full_name = objc_full_name
    assert transcoder.convert_full_name(element) == swift_full_name


def test_transcode_type_ref__nullable_prefix(transcoder):
    type_ref = make_objc_type_ref(name="MyClass", prefix="nullable ", suffix="")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_swift_type_ref(name="MyClass", prefix="", suffix="?")


def test_transcode_type_ref__nullable_suffix(transcoder):
    type_ref = make_objc_type_ref(name="MyClass", prefix="", suffix=" _Nullable")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_swift_type_ref(name="MyClass", prefix="", suffix="?")


def test_transcode_type_ref__pointer(transcoder):
    type_ref = make_objc_type_ref(name="MyClass", prefix="", suffix=" *")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_swift_type_ref(name="MyClass", prefix="", suffix="")


def test_transcode_type_ref__autoreleasing(transcoder):
    type_ref = make_objc_type_ref(name="MyClass", prefix="", suffix="*__autoreleasing")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_swift_type_ref(name="MyClass", prefix="", suffix="")


def test_transcode_type_ref__bare_id(transcoder):
    type_ref = make_objc_type_ref(name="id", prefix="", suffix="")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_swift_type_ref(id="swift-id", name="Any", prefix="", suffix="")


def test_transcode_type_ref__id_type(transcoder):
    type_ref = make_objc_type_ref(name="id",
                                  prefix="",
                                  suffix="",
                                  nested=[make_objc_type_ref(name="MyClass", prefix="", suffix="")])
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_swift_type_ref(name="MyClass", prefix="", suffix="", nested=None)


def test_transcode_type_ref__closure(transcoder):
    type_ref = make_objc_type_ref(name="",
                                  prefix="",
                                  suffix="",
                                  returns=make_objc_type_ref(name="Coordinate",
                                                             prefix="",
                                                             suffix=""),
                                  args=[
                                      make_parameter(name="arg1"),
                                      make_parameter(name="arg2",
                                                     type=make_objc_type_ref(name="MyType",
                                                                             prefix="",
                                                                             suffix="")),
                                  ])
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_swift_type_ref(name="",
                                             prefix="",
                                             suffix="",
                                             returns=make_swift_type_ref(name="Coordinate",
                                                                         prefix="",
                                                                         suffix=""),
                                             args=[
                                                 make_parameter(name="arg1"),
                                                 make_parameter(name="arg2",
                                                                type=make_swift_type_ref(
                                                                    name="MyType",
                                                                    prefix="",
                                                                    suffix="")),
                                             ])


def test_transcode_type_ref__nullable_closure(transcoder):
    type_ref = make_objc_type_ref(name="",
                                  prefix="",
                                  suffix="",
                                  returns=make_objc_type_ref(name="Coordinate",
                                                             prefix="nullable ",
                                                             suffix=""),
                                  args=[
                                      make_parameter(name="arg1"),
                                      make_parameter(name="arg2",
                                                     type=make_objc_type_ref(name="MyType",
                                                                             prefix="",
                                                                             suffix="")),
                                  ])
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_swift_type_ref(name="",
                                             prefix="",
                                             suffix="?",
                                             returns=make_swift_type_ref(name="Coordinate",
                                                                         prefix="",
                                                                         suffix=""),
                                             args=[
                                                 make_parameter(name="arg1"),
                                                 make_parameter(name="arg2",
                                                                type=make_swift_type_ref(
                                                                    name="MyType",
                                                                    prefix="",
                                                                    suffix="")),
                                             ])
