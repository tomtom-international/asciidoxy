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
"""Builders to create models for testing."""

from typing import List, Optional, Type

from asciidoxy.model import (Compound, EnumValue, InnerTypeReference, Member, Parameter,
                             ReferableElement, ReturnValue, ThrowsClause, TypeRef, TypeRefBase)


def make_referable(cls: Type[ReferableElement], lang: str, name: str) -> ReferableElement:
    element = cls(lang)
    element.id = f"{lang}-{name.lower()}"
    element.name = name
    element.full_name = f"com.asciidoxy.geometry.{name}"
    element.kind = "class"
    return element


def make_compound(lang: str,
                  name: str,
                  members: Optional[List[Member]] = None,
                  inner_classes: Optional[List[InnerTypeReference]] = None,
                  enumvalues: Optional[List[EnumValue]] = None):
    compound = make_referable(Compound, lang, name)
    if members is not None:
        compound.members = members
    if inner_classes is not None:
        compound.inner_classes = inner_classes
    compound.brief = "Brief description"
    compound.description = "Long description"
    if enumvalues is not None:
        compound.enumvalues = enumvalues
    compound.include = "include.file"
    compound.namespace = "com.asciidoxy.geometry"
    return compound


def make_member(lang: str,
                name: str,
                kind: str = "function",
                prot: str = "public",
                params: Optional[List[Parameter]] = None,
                exceptions: Optional[List[Exception]] = None,
                returns: Optional[ReturnValue] = None,
                enumvalues: Optional[List[EnumValue]] = None,
                namespace: Optional[str] = None,
                static: bool = False,
                const: bool = False,
                deleted: bool = False,
                default: bool = False) -> Member:
    member = make_referable(Member, lang, name)
    member.namespace = namespace

    if namespace:
        member.full_name = f"{namespace}.{name}"
    else:
        member.full_name = name

    member.kind = kind
    member.definition = "definition"
    member.args = "args"
    if params is not None:
        member.params = params
    if exceptions is not None:
        member.exceptions = exceptions
    member.brief = "Brief description"
    member.description = "Long description"
    member.prot = prot
    member.returns = returns
    if enumvalues is not None:
        member.enumvalues = enumvalues
    member.static = static
    member.include = "include.file"
    member.const = const
    member.deleted = deleted
    member.default = default
    return member


def make_type_ref_base(cls: Type[TypeRefBase], lang: str, name: str) -> TypeRefBase:
    type_ref = cls(lang)
    type_ref.id = f"{lang}-{name.lower()}"
    type_ref.name = name
    type_ref.namespace = "com.asciidoxy.geometry"
    return type_ref


def make_type_ref(lang: str, name: str, prefix: str = "", suffix: str = "") -> TypeRef:
    type_ref = make_type_ref_base(TypeRef, lang, name)
    type_ref.kind = "class"
    type_ref.prefix = prefix
    type_ref.suffix = suffix
    return type_ref


def make_inner_type_ref(lang: str,
                        name: str,
                        prot: str = "public",
                        element: Optional[Compound] = None) -> InnerTypeReference:
    type_ref = make_type_ref_base(InnerTypeReference, lang, name)
    type_ref.prot = prot
    type_ref.referred_object = element
    return type_ref


def make_parameter(name: str, type_: Optional[TypeRef] = None) -> Parameter:
    param = Parameter()
    param.type = type_
    param.name = name
    param.description = "Description"
    param.default_value = "42"
    return param


def make_enum_value(lang: str, name: str) -> EnumValue:
    element = make_referable(EnumValue, lang, name)
    element.initializer = " = 2"
    element.brief = "Brief description"
    element.description = "Long description"
    element.kind = "enumvalue"
    return element


def make_throws_clause(lang: str, type_ref: Optional[TypeRef] = None) -> ThrowsClause:
    clause = ThrowsClause(lang)
    if type_ref is not None:
        clause.type = type_ref
    clause.description = "Description"
    return clause


def make_return_value(type_ref: Optional[TypeRef] = None) -> ReturnValue:
    value = ReturnValue()
    value.type = type_ref
    value.description = "Description"
    return value


class SimpleClassBuilder:
    def __init__(self, lang: str):
        self.lang = lang
        self.compound = Compound(self.lang)

    def name(self, name: str):
        self.compound.name = name

    def simple_member(self, kind: str, prot: str, name: str = None, **kwargs):
        if name is None:
            name = f"{prot.capitalize()}{kind.capitalize()}"
        self.compound.members.append(
            make_member(lang=self.lang, name=name, prot=prot, kind=kind, **kwargs))

    def member_variable(self, prot: str = "public", name: str = None, type_prefix: str = ""):
        self.simple_member(kind="variable",
                           prot=prot,
                           name=name,
                           returns=make_return_value(
                               make_type_ref(self.lang, name="Type", prefix=type_prefix)))

    def member_property(self, prot: str, name: str = None):
        self.simple_member(kind="property",
                           prot=prot,
                           name=name,
                           returns=make_return_value(make_type_ref(self.lang, name="Type")))

    def member_function(self, has_return_value: bool = True, **kwargs):
        if has_return_value:
            returns = make_return_value()
        else:
            returns = None
        self.compound.members.append(
            make_member(lang=self.lang, kind="function", returns=returns, **kwargs))

    def inner_class(self, prot: str = "public", name: str = ""):
        self.compound.inner_classes.append(
            make_inner_type_ref(lang=self.lang,
                                name=name,
                                prot=prot,
                                element=make_compound(lang=self.lang, name=name)))
