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
"""Parse SourceKitten JSON to AsciiDoxy models."""

import uuid

from typing import Dict, Optional, Tuple

from ..driver_base import DriverBase
from ...model import Compound, Parameter, ReturnValue, TypeRef


class Key:
    Name = "key.name"
    Kind = "key.kind"
    Comment = "key.doc.comment"
    Substructure = "key.substructure"
    Accessibility = "key.accessibility"
    TypeName = "key.typename"


class Kind:
    Struct = "source.lang.swift.decl.struct"
    InstanceVariable = "source.lang.swift.decl.var.instance"
    InstanceMethod = "source.lang.swift.decl.function.method.instance"
    Parameter = "source.lang.swift.decl.var.parameter"


def parse_prot(value: Optional[str]) -> str:
    if not value:
        return ""

    prefix, _, prot = value.rpartition(".")
    if prefix == "source.lang.swift.accessibility":
        return prot

    return ""


def parse_kind(kind: str) -> str:
    if kind == Kind.Struct:
        return "struct"
    elif kind == Kind.InstanceVariable:
        return "variable"
    elif kind == Kind.InstanceMethod:
        return "function"
    return ""


def parse_comment(comment: Optional[str]) -> Tuple[str, str]:
    if comment:
        brief, _, description = comment.partition("\n\n")
        return brief, description
    return "", ""


def namespace_join(namespace: Optional[str], name: str) -> str:
    if namespace and name:
        return f"{namespace}.{name}"
    else:
        return name


class DocSnippets:
    """Snippets of documentation for a structure."""
    brief: str = ""
    description: str = ""
    members: Dict[str, Dict[str, str]]

    def __init__(self):
        self.members = {}

    @classmethod
    def from_comment(cls, comment: Optional[str]) -> "DocSnippets":
        snippets = cls()
        snippets.brief, snippets.description = parse_comment(comment)
        return snippets


class SwiftMarkDownCommentParser:
    def __init__(self, comment: str):
        self.comment = comment
        self.brief = []
        self.description = []
        self.fields = {}

    def parse(self) -> DocSnippets:
        for line in comment.split("\n"):
            line = line.strip()
            if not line:
                ... # empty line
            elif line.startswith("-"):
                ... # fields


class DocParser:
    """Parser for SourceKitten Doc output."""
    def __init__(self):
        self.documentation = {}

    def parse(self, data):
        for substructure in data.get(Key.Substructure, []):
            self.parse_structure(substructure)

    def parse_structure(self, data, namespace: Optional[str] = None):
        name = data.get(Key.Name)
        if not name:
            return

        full_name = namespace_join(namespace, name)
        self.documentation[full_name] = DocSnippets.from_comment(data.get(Key.Comment))

        for sub_data in data.get(Key.Substructure, []):
            self.parse_structure(sub_data, full_name)


class StructureParser:
    """Parser for SourceKitten Structure output."""
    _driver: DriverBase

    TAG: str = "swift"

    def __init__(self, driver: DriverBase, documentation):
        self._driver = driver
        self.documentation = documentation

    def parse(self, data):
        for substructure in data.get(Key.Substructure, []):
            self.parse_as_compound(substructure)

    def parse_as_compound(self, data, namespace: Optional[str] = None) -> Compound:
        compound = Compound(language=self.TAG)
        compound.name = data.get(Key.Name, "")
        compound.namespace = namespace
        compound.full_name = namespace_join(namespace, compound.name)
        compound.kind = parse_kind(data.get(Key.Kind))
        compound.prot = parse_prot(data.get(Key.Accessibility, None))
        # TODO: stable identifiers
        compound.id = str(uuid.uuid4())

        doc_snippets = self.documentation.get(compound.full_name, None)
        if doc_snippets is not None:
            compound.brief = doc_snippets.brief
            compound.description = doc_snippets.description

        if compound.kind == "struct":
            compound.members = [
                self.parse_as_compound(sub_data, compound.full_name)
                for sub_data in data.get(Key.Substructure, [])
            ]
        elif compound.kind == "function":
            compound.params = [
                self.parse_as_parameter(sub_data, namespace)
                for sub_data in data.get(Key.Substructure, [])
                if sub_data.get(Key.Kind) == Kind.Parameter
            ]
        elif compound.kind == "variable":
            type_name = data.get(Key.TypeName)
            if type_name:
                compound.returns = ReturnValue(
                    type=TypeRef(name=type_name, language=self.TAG, namespace=namespace))

        self._driver.register(compound)
        return compound

    def parse_as_parameter(self, data, namespace: Optional[str] = None) -> Parameter:
        param = Parameter()
        param.name = data.get(Key.Name, "")

        type_name = data.get(Key.TypeName)
        if type_name:
            param.type = TypeRef(name=type_name, language=self.TAG, namespace=namespace)
            self._driver.unresolved_ref(param.type)

        return param
