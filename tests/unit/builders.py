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
"""Builders to create models for testing."""

from asciidoxy.model import (Compound, Parameter, ReturnValue, ThrowsClause, TypeRef)


def make_compound(*,
                  id=None,
                  name="",
                  full_name=None,
                  language="",
                  kind="class",
                  include="include.file",
                  namespace="asciidoxy",
                  prot="public",
                  definition="definition",
                  args="args",
                  brief="Brief description",
                  description="Long description",
                  **kwargs):
    if id is None:
        id = f"{language}-{name.lower()}"
    if full_name is None:
        full_name = f"{namespace}.{name}"
    return Compound(id=id,
                    name=name,
                    language=language,
                    full_name=full_name,
                    kind=kind,
                    include=include,
                    namespace=namespace,
                    prot=prot,
                    definition=definition,
                    args=args,
                    brief=brief,
                    description=description,
                    **kwargs)


def make_parameter(*,
                   name="",
                   description="Description",
                   default_value="42",
                   prefix="out ",
                   **kwargs):
    return Parameter(name=name,
                     description=description,
                     default_value=default_value,
                     prefix=prefix,
                     **kwargs)


def make_type_ref(*,
                  id=None,
                  name="",
                  language="",
                  namespace="asciidoxy",
                  kind="class",
                  prefix="prefix",
                  suffix="suffix",
                  **kwargs):
    if id is None:
        id = f"{language}-{name.lower()}"
    return TypeRef(id=id,
                   name=name,
                   language=language,
                   namespace=namespace,
                   kind=kind,
                   prefix=prefix,
                   suffix=suffix,
                   **kwargs)


def make_throws_clause(*, language="", description="Description", **kwargs):
    return ThrowsClause(language=language, description=description, **kwargs)


def make_return_value(*, description="Description", **kwargs):
    return ReturnValue(description=description, **kwargs)


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
            make_compound(language=self.lang, name=name, prot=prot, kind=kind, **kwargs))

    def member_variable(self, prot: str = "public", name: str = None, type_prefix: str = ""):
        self.simple_member(
            kind="variable",
            prot=prot,
            name=name,
            returns=make_return_value(
                type=make_type_ref(language=self.lang, name="Type", prefix=type_prefix)))

    def member_property(self, prot: str, name: str = None):
        self.simple_member(
            kind="property",
            prot=prot,
            name=name,
            returns=make_return_value(type=make_type_ref(language=self.lang, name="Type")))

    def member_function(self, has_return_value: bool = True, **kwargs):
        if has_return_value:
            returns = make_return_value()
        else:
            returns = None
        self.compound.members.append(
            make_compound(language=self.lang, kind="function", returns=returns, **kwargs))
