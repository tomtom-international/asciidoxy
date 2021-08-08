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
"""Test base functionality for transcoding."""

import pytest

from asciidoxy.api_reference import ApiReference
from asciidoxy.transcoder.base import TranscoderBase, TranscoderError
from asciidoxy.transcoder.kotlin import KotlinTranscoder

from .builders import (make_compound, make_parameter, make_return_value, make_throws_clause,
                       make_type_ref)


class _TestTranscoder(TranscoderBase):
    SOURCE = "asm"
    TARGET = "smalltalk"


@pytest.fixture
def transcoder():
    return _TestTranscoder(ApiReference())


def test_transcode_compound__no_nested_elements(transcoder):
    compound = make_compound(language="asm", name="Coordinate", id="asm-coordinate")
    transcoded = transcoder.compound(compound)

    assert transcoded is not compound
    assert transcoded == make_compound(language="smalltalk",
                                       name="Coordinate",
                                       id="smalltalk-coordinate")
    assert compound == make_compound(language="asm", name="Coordinate", id="asm-coordinate")


def test_transcode_compound__with_members(transcoder):
    compound = make_compound(language="asm",
                             name="Coordinate",
                             members=[make_compound(language="asm", name="getLatitude")])
    transcoded = transcoder.compound(compound)

    assert transcoded is not compound
    assert transcoded == make_compound(
        language="smalltalk",
        name="Coordinate",
        members=[make_compound(language="smalltalk", name="getLatitude")])
    assert compound == make_compound(language="asm",
                                     name="Coordinate",
                                     members=[make_compound(language="asm", name="getLatitude")])


def test_transcode_compound__with_inner_classes(transcoder):
    compound = make_compound(language="asm",
                             name="Coordinate",
                             members=[
                                 make_compound(language="asm", name="Point"),
                             ])
    transcoded = transcoder.compound(compound)

    assert transcoded is not compound
    assert transcoded == make_compound(language="smalltalk",
                                       name="Coordinate",
                                       members=[
                                           make_compound(language="smalltalk", name="Point"),
                                       ])
    assert compound == make_compound(language="asm",
                                     name="Coordinate",
                                     members=[
                                         make_compound(language="asm", name="Point"),
                                     ])


def test_transcode_compound__with_params(transcoder):
    compound = make_compound(language="asm",
                             name="getLatitude",
                             namespace="Coordinate",
                             params=[
                                 make_parameter(name="arg1"),
                                 make_parameter(name="arg2",
                                                type=make_type_ref(language="asm", name="double"))
                             ])

    transcoded = transcoder.compound(compound)
    assert transcoded is not compound
    assert transcoded == make_compound(language="smalltalk",
                                       name="getLatitude",
                                       namespace="Coordinate",
                                       params=[
                                           make_parameter(name="arg1"),
                                           make_parameter(name="arg2",
                                                          type=make_type_ref(language="smalltalk",
                                                                             name="double"))
                                       ])

    assert transcoded.params[0] is not compound.params[0]
    assert transcoded.params[1] is not compound.params[1]
    assert transcoded.params[1].type is not compound.params[1].type

    assert compound == make_compound(language="asm",
                                     name="getLatitude",
                                     namespace="Coordinate",
                                     params=[
                                         make_parameter(name="arg1"),
                                         make_parameter(name="arg2",
                                                        type=make_type_ref(language="asm",
                                                                           name="double"))
                                     ])


def test_transcode_compound__with_exceptions(transcoder):
    compound = make_compound(language="asm",
                             name="getLatitude",
                             exceptions=[
                                 make_throws_clause(language="asm",
                                                    type=make_type_ref(language="asm",
                                                                       name="RuntimeException"))
                             ])
    transcoded = transcoder.compound(compound)

    assert transcoded is not compound
    assert transcoded == make_compound(language="smalltalk",
                                       name="getLatitude",
                                       exceptions=[
                                           make_throws_clause(language="smalltalk",
                                                              type=make_type_ref(
                                                                  language="smalltalk",
                                                                  name="RuntimeException"))
                                       ])
    assert compound == make_compound(language="asm",
                                     name="getLatitude",
                                     exceptions=[
                                         make_throws_clause(language="asm",
                                                            type=make_type_ref(
                                                                language="asm",
                                                                name="RuntimeException"))
                                     ])


def test_transcode_compound__with_return_value(transcoder):
    compound = make_compound(
        language="asm",
        name="getLatitude",
        returns=make_return_value(type=make_type_ref(language="asm", name="boolean")))
    transcoded = transcoder.compound(compound)

    assert transcoded is not compound
    assert transcoded == make_compound(
        language="smalltalk",
        name="getLatitude",
        returns=make_return_value(type=make_type_ref(language="smalltalk", name="boolean")))
    assert compound == make_compound(
        language="asm",
        name="getLatitude",
        returns=make_return_value(type=make_type_ref(language="asm", name="boolean")))


def test_transcode_compound__store_in_api_reference(transcoder):
    compound = make_compound(language="asm", name="Coordinate")
    transcoded = transcoder.compound(compound)
    assert transcoder.reference.find(target_id=transcoded.id) is transcoded


def test_transcode_compound__transcode_only_once(transcoder):
    compound = make_compound(language="asm", name="Coordinate")
    transcoded = transcoder.compound(compound)
    transcoded2 = transcoder.compound(compound)
    assert transcoded is transcoded2


def test_transcode_compound__transcode_inner_class_only_once(transcoder):
    inner_class = make_compound(language="asm", name="Point")
    compound = make_compound(language="asm", name="Coordinate", members=[
        inner_class,
    ])

    transcoded_inner = transcoder.compound(inner_class)
    transcoded = transcoder.compound(compound)
    assert transcoded.members[0] is transcoded_inner


def test_transcode_type_ref__no_nested_elements(transcoder):
    type_ref = make_type_ref(language="asm", name="Coordinate")
    transcoded = transcoder.type_ref(type_ref)

    assert transcoded is not type_ref
    assert transcoded == make_type_ref(language="smalltalk", name="Coordinate")
    assert type_ref == make_type_ref(language="asm", name="Coordinate")


def test_transcode_type_ref__nested_types(transcoder):
    type_ref = make_type_ref(language="asm",
                             name="Coordinate",
                             nested=[
                                 make_type_ref(language="asm", name="Point"),
                                 make_type_ref(language="asm", name="System")
                             ])
    transcoded = transcoder.type_ref(type_ref)

    assert transcoded is not type_ref
    assert transcoded == make_type_ref(language="smalltalk",
                                       name="Coordinate",
                                       nested=[
                                           make_type_ref(language="smalltalk", name="Point"),
                                           make_type_ref(language="smalltalk", name="System")
                                       ])
    assert type_ref == make_type_ref(language="asm",
                                     name="Coordinate",
                                     nested=[
                                         make_type_ref(language="asm", name="Point"),
                                         make_type_ref(language="asm", name="System")
                                     ])


def test_transcode_type_ref__args(transcoder):
    type_ref = make_type_ref(language="asm",
                             returns=make_type_ref(language="asm", name="Coordinate"),
                             args=[
                                 make_parameter(name="arg1"),
                                 make_parameter(name="arg2",
                                                type=make_type_ref(language="asm",
                                                                   name="MyType",
                                                                   prefix="final ",
                                                                   suffix=" *")),
                             ])
    transcoded = transcoder.type_ref(type_ref)

    assert transcoded is not type_ref
    assert transcoded == make_type_ref(language="smalltalk",
                                       returns=make_type_ref(language="smalltalk",
                                                             name="Coordinate"),
                                       args=[
                                           make_parameter(name="arg1"),
                                           make_parameter(name="arg2",
                                                          type=make_type_ref(language="smalltalk",
                                                                             name="MyType",
                                                                             prefix="final ",
                                                                             suffix=" *")),
                                       ])
    assert type_ref == make_type_ref(language="asm",
                                     returns=make_type_ref(language="asm", name="Coordinate"),
                                     args=[
                                         make_parameter(name="arg1"),
                                         make_parameter(name="arg2",
                                                        type=make_type_ref(language="asm",
                                                                           name="MyType",
                                                                           prefix="final ",
                                                                           suffix=" *")),
                                     ])


def test_transcode_parameter__no_type(transcoder):
    param = make_parameter(name="argument")
    transcoded = transcoder.parameter(param)

    assert transcoded is not param
    assert transcoded == make_parameter(name="argument")
    assert param == make_parameter(name="argument")


def test_transcode_parameter__with_type(transcoder):
    param = make_parameter(name="argument", type=make_type_ref(language="asm", name="MyType"))
    transcoded = transcoder.parameter(param)

    assert transcoded is not param
    assert transcoded == make_parameter(name="argument",
                                        type=make_type_ref(language="smalltalk", name="MyType"))
    assert param == make_parameter(name="argument",
                                   type=make_type_ref(language="asm", name="MyType"))


def test_transcode_return_value__no_type(transcoder):
    ret_val = make_return_value()
    transcoded = transcoder.return_value(ret_val)

    assert transcoded is not ret_val
    assert transcoded == make_return_value()
    assert ret_val == make_return_value()


def test_transcode_return_value__with_type(transcoder):
    ret_val = make_return_value(type=make_type_ref(language="asm", name="MyType"))
    transcoded = transcoder.return_value(ret_val)

    assert transcoded is not ret_val
    assert transcoded == make_return_value(type=make_type_ref(language="smalltalk", name="MyType"))
    assert ret_val == make_return_value(type=make_type_ref(language="asm", name="MyType"))


def test_transcode_throws_clause(transcoder):
    throws_clause = make_throws_clause(language="asm",
                                       type=make_type_ref(language="asm", name="MyType"))
    transcoded = transcoder.throws_clause(throws_clause)

    assert transcoded is not throws_clause
    assert transcoded == make_throws_clause(language="smalltalk",
                                            type=make_type_ref(language="smalltalk", name="MyType"))
    assert throws_clause == make_throws_clause(language="asm",
                                               type=make_type_ref(language="asm", name="MyType"))


def test_transcode__load_and_detect_transcoders():
    instance = TranscoderBase.instance("java", "kotlin", ApiReference())
    assert instance is not None
    assert isinstance(instance, KotlinTranscoder)


def test_transcode__compound():
    compound = make_compound(language="java", name="Coordinate")
    transcoded = TranscoderBase.transcode(compound, "kotlin", ApiReference())
    assert transcoded.language == "kotlin"


def test_transcode__not_supported():
    compound = make_compound(language="java", name="Coordinate")
    with pytest.raises(TranscoderError):
        TranscoderBase.transcode(compound, "cpp", ApiReference())
