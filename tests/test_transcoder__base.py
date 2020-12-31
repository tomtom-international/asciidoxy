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
"""Test base functionality for transcoding."""

import pytest

from asciidoxy.api_reference import ApiReference
from asciidoxy.model import ReturnValue, ThrowsClause
from asciidoxy.transcoder.base import TranscoderBase, TranscoderError
from asciidoxy.transcoder.kotlin import KotlinTranscoder

from .builders import (make_compound, make_member, make_type_ref, make_inner_type_ref,
                       make_parameter, make_enum_value, make_throws_clause, make_return_value)


class _TestTranscoder(TranscoderBase):
    SOURCE = "asm"
    TARGET = "smalltalk"


@pytest.fixture
def transcoder():
    return _TestTranscoder(ApiReference())


def test_transcode_compound__no_nested_elements(transcoder):
    compound = make_compound("asm", "Coordinate")

    transcoded = transcoder.compound(compound)

    assert transcoded.id == "smalltalk-coordinate"
    assert transcoded.name == "Coordinate"
    assert transcoded.full_name == "com.asciidoxy.geometry.Coordinate"
    assert transcoded.language == "smalltalk"
    assert transcoded.kind == "class"
    assert not transcoded.members
    assert not transcoded.inner_classes
    assert transcoded.brief == "Brief description"
    assert transcoded.description == "Long description"
    assert not transcoded.enumvalues
    assert transcoded.include == "include.file"
    assert transcoded.namespace == "com.asciidoxy.geometry"

    assert compound.id == "asm-coordinate"
    assert compound.language == "asm"


def test_transcode_compound__members(transcoder):
    compound = make_compound("asm", "Coordinate", members=[make_member("asm", "getLatitude")])

    transcoded = transcoder.compound(compound)

    assert len(transcoded.members) == 1
    assert transcoded.members[0]
    assert transcoded.members[0].id == "smalltalk-getlatitude"
    assert transcoded.members[0].language == "smalltalk"

    assert compound.members[0].id == "asm-getlatitude"
    assert compound.members[0].language == "asm"


def test_transcode_compound__inner_classes(transcoder):
    compound = make_compound("asm",
                             "Coordinate",
                             inner_classes=[
                                 make_inner_type_ref(lang="asm",
                                                     name="Point",
                                                     element=make_compound("asm", "Point"))
                             ])

    transcoded = transcoder.compound(compound)

    assert len(transcoded.inner_classes) == 1
    assert transcoded.inner_classes[0]
    assert transcoded.inner_classes[0].id == "smalltalk-point"
    assert transcoded.inner_classes[0].language == "smalltalk"
    assert transcoded.inner_classes[0].referred_object
    assert transcoded.inner_classes[0].referred_object.id == "smalltalk-point"
    assert transcoded.inner_classes[0].referred_object.language == "smalltalk"

    assert compound.inner_classes[0].id == "asm-point"
    assert compound.inner_classes[0].language == "asm"
    assert compound.inner_classes[0].referred_object.id == "asm-point"
    assert compound.inner_classes[0].referred_object.language == "asm"


def test_transcode_compound__enumvalues(transcoder):
    compound = make_compound("asm", "Coordinate", enumvalues=[make_enum_value("asm", "WGS84")])

    transcoded = transcoder.compound(compound)

    assert len(transcoded.enumvalues) == 1
    assert transcoded.enumvalues[0]
    assert transcoded.enumvalues[0].id == "smalltalk-wgs84"
    assert transcoded.enumvalues[0].language == "smalltalk"

    assert compound.enumvalues[0].id == "asm-wgs84"
    assert compound.enumvalues[0].language == "asm"


def test_transcode_compound__store_in_api_reference(transcoder):
    compound = make_compound("asm", "Coordinate")
    transcoded = transcoder.compound(compound)
    assert transcoder.reference.find(target_id=transcoded.id) is transcoded


def test_transcode_compound__transcode_only_once(transcoder):
    compound = make_compound("asm", "Coordinate")
    transcoded = transcoder.compound(compound)
    transcoded2 = transcoder.compound(compound)
    assert transcoded is transcoded2


def test_transcode_compound__transcode_inner_class_only_once(transcoder):
    inner_class = make_compound(lang="asm", name="Point")
    compound = make_compound(
        lang="asm",
        name="Coordinate",
        inner_classes=[make_inner_type_ref(lang="asm", name="Point", element=inner_class)])

    transcoded_inner = transcoder.compound(inner_class)
    transcoded = transcoder.compound(compound)
    assert transcoded.inner_classes[0].referred_object is transcoded_inner


def test_transcode_member__no_nested_elements(transcoder):
    member = make_member(lang="asm",
                         name="getLatitude",
                         namespace="com.asciidoxy.geometry",
                         const=True)

    transcoded = transcoder.member(member)

    assert transcoded.id == "smalltalk-getlatitude"
    assert transcoded.name == "getLatitude"
    assert transcoded.full_name == "com.asciidoxy.geometry.getLatitude"
    assert transcoded.language == "smalltalk"
    assert transcoded.kind == "function"
    assert transcoded.definition == "definition"
    assert transcoded.args == "args"
    assert transcoded.brief == "Brief description"
    assert transcoded.description == "Long description"
    assert transcoded.prot == "public"
    assert transcoded.static is False
    assert transcoded.include == "include.file"
    assert transcoded.namespace == "com.asciidoxy.geometry"
    assert transcoded.const is True
    assert transcoded.deleted is False
    assert transcoded.default is False

    assert not transcoded.params
    assert not transcoded.exceptions
    assert not transcoded.returns
    assert not transcoded.enumvalues

    assert member.id == "asm-getlatitude"
    assert member.language == "asm"


def test_transcode_member__with_params(transcoder):
    member = make_member(
        "asm",
        "getLatitude",
        params=[make_parameter("arg1"),
                make_parameter("arg2", make_type_ref("asm", "double"))])

    transcoded = transcoder.member(member)

    assert len(transcoded.params) == 2
    assert not transcoded.params[0].type
    assert transcoded.params[0].name == "arg1"
    assert transcoded.params[0].description == "Description"
    assert transcoded.params[1].type
    assert transcoded.params[1].type.id == "smalltalk-double"
    assert transcoded.params[1].type.language == "smalltalk"
    assert transcoded.params[1].name == "arg2"
    assert transcoded.params[1].description == "Description"

    assert member.params[1].type.id == "asm-double"
    assert member.params[1].type.language == "asm"


def test_transcode_member__with_exceptions(transcoder):
    member = make_member(
        "asm",
        "getLatitude",
        exceptions=[make_throws_clause("asm", make_type_ref("asm", "RuntimeException"))])

    transcoded = transcoder.member(member)

    assert len(transcoded.exceptions) == 1
    assert transcoded.exceptions[0].type
    assert transcoded.exceptions[0].type.id == "smalltalk-runtimeexception"
    assert transcoded.exceptions[0].type.language == "smalltalk"
    assert transcoded.exceptions[0].description == "Description"

    assert member.exceptions[0].type.id == "asm-runtimeexception"
    assert member.exceptions[0].type.language == "asm"


def test_transcode_member__with_return_value(transcoder):
    member = make_member("asm",
                         "getLatitude",
                         returns=make_return_value(make_type_ref("asm", "boolean")))

    transcoded = transcoder.member(member)

    assert transcoded.returns
    assert transcoded.returns.type
    assert transcoded.returns.type.id == "smalltalk-boolean"
    assert transcoded.returns.type.language == "smalltalk"
    assert transcoded.returns.description == "Description"

    assert member.returns.type.id == "asm-boolean"
    assert member.returns.type.language == "asm"


def test_transcode_member__with_enum_values(transcoder):
    member = make_member(
        "asm",
        "CoordinateType",
        enumvalues=[make_enum_value("asm", "TypeA"),
                    make_enum_value("asm", "TypeB")])

    transcoded = transcoder.member(member)

    assert len(transcoded.enumvalues) == 2
    assert transcoded.enumvalues[0].id == "smalltalk-typea"
    assert transcoded.enumvalues[0].language == "smalltalk"
    assert transcoded.enumvalues[1].id == "smalltalk-typeb"
    assert transcoded.enumvalues[1].language == "smalltalk"

    assert member.enumvalues[0].id == "asm-typea"
    assert member.enumvalues[0].language == "asm"
    assert member.enumvalues[1].id == "asm-typeb"
    assert member.enumvalues[1].language == "asm"


def test_transcode_member__store_in_api_reference(transcoder):
    member = make_member("asm", "getLatitude")
    transcoded = transcoder.member(member)
    assert transcoder.reference.find(target_id=transcoded.id) is transcoded


def test_transcode_member__transcode_only_once(transcoder):
    member = make_member("asm", "getLatitude")
    transcoded = transcoder.member(member)
    transcoded2 = transcoder.member(member)
    assert transcoded is transcoded2


def test_transcode_type_ref__no_nested_elements(transcoder):
    type_ref = make_type_ref("asm", "Coordinate", prefix="final ", suffix=" *")

    transcoded = transcoder.type_ref(type_ref)

    assert transcoded is not type_ref

    assert transcoded.language == "smalltalk"
    assert transcoded.id == "smalltalk-coordinate"
    assert transcoded.name == "Coordinate"
    assert transcoded.namespace == "com.asciidoxy.geometry"
    assert transcoded.kind == "class"
    assert transcoded.prefix == "final "
    assert transcoded.suffix == " *"
    assert not transcoded.nested
    assert not transcoded.args

    assert type_ref.language == "asm"
    assert type_ref.id == "asm-coordinate"
    assert type_ref.name == "Coordinate"
    assert type_ref.namespace == "com.asciidoxy.geometry"
    assert type_ref.kind == "class"
    assert type_ref.prefix == "final "
    assert type_ref.suffix == " *"


def test_transcode_type_ref__nested_types(transcoder):
    type_ref = make_type_ref("asm", "Coordinate", prefix="final ", suffix=" *")
    type_ref.nested = [
        make_type_ref("asm", "Point", prefix="final ", suffix=" *"),
        make_type_ref("asm", "System", prefix="final ", suffix=" *")
    ]

    transcoded = transcoder.type_ref(type_ref)

    assert transcoded is not type_ref

    assert transcoded.language == "smalltalk"
    assert transcoded.id == "smalltalk-coordinate"
    assert transcoded.name == "Coordinate"
    assert transcoded.namespace == "com.asciidoxy.geometry"
    assert transcoded.kind == "class"
    assert transcoded.prefix == "final "
    assert transcoded.suffix == " *"
    assert not transcoded.args
    assert len(transcoded.nested) == 2

    assert transcoded.nested[0].id == "smalltalk-point"
    assert transcoded.nested[0].name == "Point"
    assert transcoded.nested[0].language == "smalltalk"
    assert transcoded.nested[1].id == "smalltalk-system"
    assert transcoded.nested[1].name == "System"
    assert transcoded.nested[1].language == "smalltalk"

    assert type_ref.language == "asm"
    assert type_ref.id == "asm-coordinate"
    assert type_ref.name == "Coordinate"
    assert type_ref.namespace == "com.asciidoxy.geometry"
    assert type_ref.kind == "class"
    assert type_ref.prefix == "final "
    assert type_ref.suffix == " *"


def test_transcode_type_ref__args(transcoder):
    type_ref = make_type_ref("asm", name="", prefix="final ", suffix=" *")
    type_ref.returns = make_type_ref("asm", "Coordinate", prefix="final ", suffix=" *")
    type_ref.args = [
        make_parameter("arg1"),
        make_parameter("arg2", make_type_ref("asm", "MyType", prefix="final ", suffix=" *")),
    ]

    transcoded = transcoder.type_ref(type_ref)

    assert transcoded is not type_ref

    assert transcoded.language == "smalltalk"
    assert not transcoded.name
    assert not transcoded.nested
    assert len(transcoded.args) == 2
    assert transcoded.returns is not None

    assert not transcoded.args[0].type
    assert transcoded.args[0].name == "arg1"
    assert transcoded.args[0].description == "Description"

    assert transcoded.args[1].type
    assert transcoded.args[1].type.name == "MyType"
    assert transcoded.args[1].type.id == "smalltalk-mytype"
    assert transcoded.args[1].type.language == "smalltalk"
    assert transcoded.args[1].name == "arg2"
    assert transcoded.args[1].description == "Description"

    assert type_ref.args[1].type.id == "asm-mytype"
    assert type_ref.args[1].type.language == "asm"

    assert transcoded.returns.language == "smalltalk"
    assert transcoded.returns.name == "Coordinate"


def test_transcode_parameter__no_type(transcoder):
    param = make_parameter("argument")

    transcoded = transcoder.parameter(param)

    assert not transcoded.type
    assert transcoded.name == "argument"
    assert transcoded.description == "Description"
    assert transcoded.default_value == "42"


def test_transcode_parameter__with_type(transcoder):
    param = make_parameter("argument", make_type_ref("asm", "MyType", prefix="final ", suffix=" *"))

    transcoded = transcoder.parameter(param)

    assert transcoded.type
    assert transcoded.type.language == "smalltalk"
    assert transcoded.type.name == "MyType"
    assert transcoded.name == "argument"
    assert transcoded.description == "Description"
    assert transcoded.default_value == "42"

    assert param.type.language == "asm"


def test_transcode_return_value__no_type(transcoder):
    ret_val = ReturnValue()
    ret_val.description = "Description"

    transcoded = transcoder.return_value(ret_val)

    assert transcoded.type is None
    assert transcoded.description == "Description"


def test_transcode_return_value__with_type(transcoder):
    ret_val = ReturnValue()
    ret_val.description = "Description"
    ret_val.type = make_type_ref("asm", "MyType", prefix="final ", suffix=" *")

    transcoded = transcoder.return_value(ret_val)

    assert transcoded.type
    assert transcoded.type.language == "smalltalk"
    assert transcoded.type.name == "MyType"
    assert transcoded.description == "Description"

    assert ret_val.type.language == "asm"


def test_transcode_throws_clause(transcoder):
    ret_val = ThrowsClause("asm")
    ret_val.description = "Description"
    ret_val.type = make_type_ref("asm", "MyType", prefix="final ", suffix=" *")

    transcoded = transcoder.throws_clause(ret_val)

    assert transcoded.type
    assert transcoded.type.language == "smalltalk"
    assert transcoded.type.name == "MyType"
    assert transcoded.description == "Description"

    assert ret_val.type.language == "asm"


def test_transcode_enum_value(transcoder):
    enum_value = make_enum_value("asm", "SomeValue")

    transcoded = transcoder.enum_value(enum_value)

    assert transcoded.id == "smalltalk-somevalue"
    assert transcoded.name == "SomeValue"
    assert transcoded.full_name == "com.asciidoxy.geometry.SomeValue"
    assert transcoded.language == "smalltalk"
    assert transcoded.kind == "enumvalue"
    assert transcoded.initializer == " = 2"
    assert transcoded.brief == "Brief description"
    assert transcoded.description == "Long description"

    assert enum_value.id == "asm-somevalue"
    assert enum_value.language == "asm"


def test_transcode_enum_value__store_in_api_reference(transcoder):
    enum_value = make_enum_value("asm", "SomeValue")
    transcoded = transcoder.enum_value(enum_value)
    assert transcoder.reference.find(target_id=transcoded.id) is transcoded


def test_transcode_enum_value__transcode_only_once(transcoder):
    enum_value = make_enum_value("asm", "SomeValue")
    transcoded = transcoder.enum_value(enum_value)
    transcoded2 = transcoder.enum_value(enum_value)
    assert transcoded is transcoded2


def test_transcode_inner_type_reference__empty(transcoder):
    ref = make_inner_type_ref("asm", "Coordinate")

    transcoded = transcoder.inner_type_reference(ref)
    assert transcoded.language == "smalltalk"
    assert transcoded.id == "smalltalk-coordinate"
    assert transcoded.name == "Coordinate"
    assert transcoded.namespace == "com.asciidoxy.geometry"
    assert not transcoded.referred_object

    assert ref.language == "asm"
    assert ref.id == "asm-coordinate"
    assert ref.name == "Coordinate"
    assert ref.namespace == "com.asciidoxy.geometry"


def test_transcode_inner_type_reference__referred_object(transcoder):
    ref = make_inner_type_ref(lang="asm",
                              name="Coordinate",
                              element=make_compound("asm", "Coordinate"))

    transcoded = transcoder.inner_type_reference(ref)

    assert transcoded.referred_object
    assert transcoded.referred_object.id == "smalltalk-coordinate"
    assert transcoded.referred_object.language == "smalltalk"

    assert ref.referred_object.id == "asm-coordinate"
    assert ref.referred_object.language == "asm"


def test_transcode__load_and_detect_transcoders():
    instance = TranscoderBase.instance("java", "kotlin", ApiReference())
    assert instance is not None
    assert isinstance(instance, KotlinTranscoder)


def test_transcode__compound():
    compound = make_compound("java", "Coordinate")
    transcoded = TranscoderBase.transcode(compound, "kotlin", ApiReference())
    assert transcoded.language == "kotlin"


def test_transcode__member():
    member = make_member("java", "Coordinate")
    transcoded = TranscoderBase.transcode(member, "kotlin", ApiReference())
    assert transcoded.language == "kotlin"


def test_transcode__not_supported():
    member = make_member("java", "Coordinate")
    with pytest.raises(TranscoderError):
        TranscoderBase.transcode(member, "cpp", ApiReference())
