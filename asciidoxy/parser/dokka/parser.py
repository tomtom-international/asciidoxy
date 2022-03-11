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
"""Read API reference information from AsciiDoxy-Dokka JSON output."""
from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, TypeVar, Union

from ...model import Compound, Parameter, ReferableElement, ReturnValue, TypeRef
from ..doxygen.description_parser import ParaContainer, parse_description, select_descriptions
from ..factory import ReferenceParserBase

logger = logging.getLogger(__name__)


def _dri_clean(value: str) -> str:
    return value.replace("#", "2_").replace(".", "1_1_")


def _join(sep: str, *values: str) -> str:
    return sep.join((v for v in values if v))


class Description(NamedTuple):
    brief: str = ""
    detailed: str = ""

    @staticmethod
    def parse(description: str) -> Description:
        if not description:
            return Description()

        contents = parse_description(ET.fromstring(description), "kotlin")
        return Description(*select_descriptions(ParaContainer("kotlin"), contents))


def parse_single_description(description: str) -> str:
    return parse_description(ET.fromstring(description), "kotlin").to_asciidoc()


class DRI(NamedTuple):
    package_name: str = ""
    class_names: str = ""
    callable_name: str = ""
    callable_signature: str = ""
    target: str = ""
    extra: str = ""

    @staticmethod
    def parse(dri_string: str) -> DRI:
        return DRI(*dri_string.split("/"))

    @property
    def id(self) -> str:
        return _join("1_1_", _dri_clean(self.package_name), self.class_names, self.callable_name,
                     _dri_clean(self.callable_signature))

    @property
    def name(self) -> str:
        return self.callable_name or self.class_names or self.package_name

    @property
    def full_name(self) -> str:
        return _join(".", self.package_name, self.class_names, self.callable_name)

    @property
    def namespace(self) -> str:
        if self.callable_name:
            return _join(".", self.package_name, self.class_names)
        else:
            return self.package_name


_ReferableElement = TypeVar("_ReferableElement", bound=ReferableElement)


class Parser(ReferenceParserBase):
    """Parse AsciiDoxy-Dokka JSON output."""

    TAG: str = "kotlin"

    def parse(self, reference_path: Union[Path, str]) -> bool:
        """Parse reference documentation from the given path.

        Args:
            reference_path File or directory containing the reference documentation.

        Returns:
            True if the reference has been parsed. False if the reference path does not contain
            valid content for this parser.
        """
        reference_path = Path(reference_path)
        if reference_path.is_file():
            return self._parse_file(reference_path)
        else:
            for json_file in reference_path.glob("**/*.json"):
                if not self._parse_file(json_file):
                    return False
            return True

    def _parse_file(self, file: Path) -> bool:
        with file.open("r") as file_handle:
            json.load(file_handle, object_hook=self._parse_object)
        return True

    def _parse_object(self, data: Dict[str, Any]) -> Any:
        obj_type = data.get("type")
        if not obj_type:
            return data

        if obj_type == "org.asciidoxy.dokka.JsonDClasslike":
            return self._parse_compound(data)
        elif obj_type == "org.asciidoxy.dokka.JsonDFunction":
            return self._parse_compound(data)
        elif obj_type == "org.asciidoxy.dokka.JsonDProperty":
            return self._parse_compound(data)
        elif obj_type == "org.asciidoxy.dokka.JsonDParameter":
            return self._parse_parameter(data)
        elif obj_type == "org.asciidoxy.dokka.JsonGenericTypeConstructor":
            return self._parse_typeref(data)
        elif obj_type == "org.asciidoxy.dokka.JsonDPackage":
            # Ignore
            return None
        else:
            logger.error(f"Unexpected type: {obj_type}")
            return None

    def _determine_kind(self, dokka_type: Optional[str]) -> str:
        if not dokka_type:
            return ""
        namespace, _, name = dokka_type.rpartition(".")
        if namespace == "org.asciidoxy.dokka":
            return name[5:].lower()
        else:
            return name.lower()

    def _make_id(self, dri: DRI) -> str:
        return f"{self.TAG}-{dri.id}"

    def _register(self, element: _ReferableElement) -> _ReferableElement:
        self.api_reference.append(element)
        return element

    def _parse_compound(self, data: Dict[str, Any]) -> Compound:
        dri = DRI.parse(data["dri"])
        name = data.get("name") or dri.name

        if "returnType" in data:
            return_value = ReturnValue(type=data["returnType"])
        else:
            return_value = None

        if data.get("isConstructor", False):
            kind = "constructor"
        elif "kind" in data:
            kind = data["kind"]
        else:
            kind = self._determine_kind(data.get("type"))

        if "modifier" in data:
            modifiers = [data["modifier"]]
        else:
            modifiers = []

        description = Description()
        docs = data.get("docs")
        if docs:
            if "Description" in docs:
                description = Description.parse(docs["Description"])
            else:
                obj_doc_name = f"{kind.title()}: {name}"
                if obj_doc_name in docs:
                    description = Description.parse(docs[obj_doc_name])

            if return_value is not None and "Return" in docs:
                return_value.description = parse_single_description(docs["Return"])

        return self._register(
            Compound(
                language=self.TAG,
                id=self._make_id(dri),
                name=name,
                full_name=dri.full_name,
                namespace=dri.namespace,
                kind=kind,
                prot=data.get("visibility", ""),
                modifiers=modifiers,
                returns=return_value,
                members=data.get("children", []),
                params=data.get("parameters", []),
                brief=description.brief,
                description=description.detailed,
            ))

    def _parse_typeref(self, data: Dict[str, Any]) -> TypeRef:
        dri = DRI.parse(data["dri"])
        name = data.get("presentableName") or dri.name

        # TODO: Handle links to types in other packages and stdlib
        if dri.package_name != "kotlin":
            id = self._make_id(dri)
        else:
            id = None

        return TypeRef(
            language=self.TAG,
            id=id,
            name=name,
        )

    def _parse_parameter(self, data: Dict[str, Any]) -> Parameter:
        name = data["name"]
        description = ""

        docs = data.get("docs")
        if docs:
            obj_doc_name = f"Property: {name}"
            if obj_doc_name in docs:
                description = parse_single_description(docs[obj_doc_name])

        return Parameter(
            type=data["parameterType"],
            name=name,
            description=description,
        )
