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
"""Read API reference information from Doxygen XML output."""

import functools
import logging
import re

import xml.etree.ElementTree as ET

from typing import List, Mapping, Optional, Pattern, Set, Tuple, Union

from .api_reference import AmbiguousLookupError, ApiReference
from .model import (Compound, EnumValue, Member, Parameter, ReturnValue, ThrowsClause, TypeRef,
                    InnerTypeReference, ReferableElement, TypeRefBase)

logger = logging.getLogger(__name__)


def _yes_no_to_bool(yes_no: str) -> bool:
    if yes_no == "yes":
        return True
    return False


def _select_descriptions(brief: str, detailed: str) -> Tuple[str, str]:
    if not brief and detailed:
        if "\n" in detailed:
            brief, detailed = detailed.split("\n", maxsplit=1)
            return brief, detailed.strip()
        return detailed, ""

    return brief, detailed


class DescriptionParser(object):
    """Parse a description from XML and convert it to AsciiDoc.

    Attributes:
        language: Language to parse and return.
    """

    language: str
    _parts: List[str]

    def __init__(self, language: str):
        self.language = language
        self._parts = []

    def parse(self, element: ET.Element) -> str:
        """Parse a description from XML and convert it to AsciiDoc.

        Args:
            element: XML element to convert to AsciiDoc text.

        Returns:
            AsciiDoc text representation of the element.
        """
        self._parts = []
        self.parse_children(element)
        text = "".join(self._parts).strip()

        # Remove spaces before a line break
        text = re.sub(" *$", "", text, flags=re.MULTILINE)

        # Remove single space on new line
        text = re.sub(r"^ (\S)", r"\1", text, flags=re.MULTILINE)

        # No more than 2 consecutive line breaks
        text = re.sub("\n{3,}", "\n\n", text)

        return text

    def parse_children(self, element: ET.Element) -> None:
        for sub_element in element:
            method = getattr(self, f"parse_{sub_element.tag}")
            method(sub_element)

    def _default_parse(self, element: ET.Element, prefix=None, suffix=None) -> None:
        self.append(prefix)
        self.append(DescriptionParser._strip_line_ends(element.text))
        self.parse_children(element)
        self.append(suffix)
        self.append(DescriptionParser._strip_line_ends(element.tail))

    @staticmethod
    def _strip_line_ends(text: Optional[str]) -> Optional[str]:
        if text is None:
            return None
        return re.sub("\n$", " ", text, flags=re.MULTILINE)

    parse_para = functools.partialmethod(_default_parse, suffix="\n\n")
    parse_itemizedlist = functools.partialmethod(_default_parse, prefix="\n\n", suffix="\n")
    parse_listitem = functools.partialmethod(_default_parse, prefix="* ")
    parse_bold = functools.partialmethod(_default_parse, prefix="**", suffix="**")
    parse_computeroutput = functools.partialmethod(_default_parse, prefix="`", suffix="`")
    parse_codeline = functools.partialmethod(_default_parse, suffix="\n")
    parse_sp = functools.partialmethod(_default_parse, prefix=" ")

    def parse_ulink(self, element: ET.Element) -> None:
        self._default_parse(element, prefix=f"{element.get('url')}[", suffix="]")

    def parse_ref(self, element: ET.Element) -> None:
        self._default_parse(element,
                            prefix=f"xref:{self.language}-{element.get('refid')}[",
                            suffix="]")

    def parse_parameterlist(self, element) -> None:
        pass

    def parse_simplesect(self, element: ET.Element) -> None:
        kind = element.get("kind")
        if kind in ["note", "tip", "important", "caution", "warning"]:
            self._default_parse(element, prefix=f"\n[{kind.upper()}]\n====\n", suffix="====\n")

    def parse_programlisting(self, element: ET.Element) -> None:
        self._default_parse(element, prefix=f"\n[source,{self.language}]\n----\n", suffix="----\n")

    def parse_highlight(self, element: ET.Element) -> None:
        if element.get("class") == "normal":
            self._default_parse(element)
        else:
            self._default_parse(element, prefix="__", suffix="__")

    def __getattr__(self, name):
        return self._default_parse

    def append(self, text: Optional[str]) -> None:
        if text:
            self._parts.append(text)


class Language(object):
    """Definition of language support for parsing Doxygen XML output.

    Attributes:
        TAG:                   Tag for identifying the language.
        TYPE_PREFIXES:         Pattern matching text that is not part of the type name, but instead
                                   is a prefix to the type.
        TYPE_SUFFIXES:         Pattern matching text that is not part of the type name, but instead
                                   is a suffix to the type.
        TYPE_NESTED_START:     Pattern matching the start of a nested type.
        TYPE_NESTED_SEPARATOR: Pattern matching a separator between multiple nested types.
        TYPE_NESTED_END:       Pattern matching the end of a nested type.
        TYPE_NAME:             Pattern matching a type's name.
    """

    TAG: str

    TYPE_PREFIXES: Pattern
    TYPE_SUFFIXES: Pattern
    TYPE_NESTED_START: Pattern
    TYPE_NESTED_SEPARATOR: Pattern
    TYPE_NESTED_END: Pattern
    TYPE_NAME: Pattern

    _parser: "DoxygenXmlParser"

    def __init__(self, parser: "DoxygenXmlParser"):
        self._parser = parser

    def parse_description(self, description_element: Optional[ET.Element]) -> str:
        if description_element is None:
            return ""

        return DescriptionParser(self.TAG).parse(description_element)

    def parse_parameterlist(self, memberdef_element: ET.Element,
                            kind: str) -> List[Tuple[str, str]]:
        descriptions = []
        for parameter_item in memberdef_element.iterfind(
                f"detaileddescription/para/parameterlist[@kind='{kind}']/parameteritem"):
            desc = self.parse_description(parameter_item.find("parameterdescription"))
            for parameter_name in parameter_item.iterfind("parameternamelist/parametername"):
                if parameter_name.text:
                    descriptions.append((parameter_name.text, desc))
        return descriptions

    def parse_parameters(self, memberdef_element: ET.Element, parent: Member) -> List[Parameter]:
        descriptions = self.parse_parameterlist(memberdef_element, "param")
        params = []
        for param_element in memberdef_element.iterfind("param"):
            param = Parameter()
            param.type = self.parse_type(param_element.find("type"), parent)
            param.name = param_element.findtext("declname") or ""

            matching_descriptions = [desc for name, desc in descriptions if name == param.name]
            if matching_descriptions:
                if len(matching_descriptions) > 1:
                    logger.debug(f"Multiple descriptions for parameter {param.name}")
                param.description = matching_descriptions[0]

            params.append(param)
        return params

    def parse_type(self,
                   type_element: Optional[ET.Element],
                   parent: Optional[Union[Compound, Member]] = None) -> Optional[TypeRef]:
        if type_element is None:
            return None

        def match_and_extract(regex, text):
            if text:
                match = regex.match(text)
                if match:
                    return match.group(0), text[match.end():]

            return None, text

        def extract_type(element_iter, text):
            type_ref = TypeRef(self.TAG)
            if isinstance(parent, Compound):
                type_ref.namespace = parent.full_name
            elif isinstance(parent, Member):
                type_ref.namespace = parent.namespace

            type_ref.prefix, text = match_and_extract(self.TYPE_PREFIXES, text)

            if not text:
                try:
                    element = next(element_iter)
                    type_ref.id = self.unique_id(element.get("refid"))
                    type_ref.kind = element.get("kindref", None)
                    type_ref.name = self.cleanup_name(element.text or "")
                    text = element.tail

                except StopIteration:
                    pass
            else:
                type_ref.name, text = match_and_extract(self.TYPE_NAME, text)
                if type_ref.name is not None:
                    type_ref.name = self.cleanup_name(type_ref.name)

            start_nested, text = match_and_extract(self.TYPE_NESTED_START, text)
            if start_nested:
                while True:
                    nested_type_ref, text = extract_type(element_iter, text)
                    if nested_type_ref and nested_type_ref.name:
                        type_ref.nested.append(nested_type_ref)
                    else:
                        # TODO Error?
                        break

                    end_nested, text = match_and_extract(self.TYPE_NESTED_END, text)
                    if end_nested:
                        break

                    _, text = match_and_extract(self.TYPE_NESTED_SEPARATOR, text)

            type_ref.suffix, text = match_and_extract(self.TYPE_SUFFIXES, text)

            # doxygen inserts empty <type> tag for return value in constructors,
            # this fake types should be filtered out
            if type_ref.name:
                if not type_ref.id and not self.is_language_standard_type(type_ref.name):
                    self._parser.unresolved_ref(type_ref)

            return type_ref, text

        type_ref, _ = extract_type(type_element.iter("ref"), type_element.text)

        if type_ref.name:
            return type_ref
        else:
            return None

    def parse_exceptions(self, memberdef_element: ET.Element, parent: Member) -> List[ThrowsClause]:
        exceptions = []
        for name, desc in self.parse_parameterlist(memberdef_element, "exception"):
            exception = ThrowsClause(self.TAG)
            exception.type = TypeRef(name=name, language=self.TAG)
            exception.type.namespace = parent.namespace
            exception.description = desc
            exceptions.append(exception)
            self._parser.unresolved_ref(exception.type)
        return exceptions

    def parse_returns(self, memberdef_element: ET.Element, parent: Member) -> Optional[ReturnValue]:
        returns = ReturnValue()
        returns.type = self.parse_type(memberdef_element.find("type"), parent)

        description = memberdef_element.find("detaileddescription/para/simplesect[@kind='return']")
        if description:
            returns.description = self.parse_description(description)

        if returns.type:
            return returns
        else:
            return None

    def parse_enumvalues(self, container_element: ET.Element, parent_name: str) -> List[EnumValue]:
        values = []
        for enumvalue_element in container_element.iterfind("enumvalue"):
            v = EnumValue(self.TAG)
            v.id = self.unique_id(enumvalue_element.get("id"))

            name = self.cleanup_name(enumvalue_element.findtext("name", ""))
            v.name = self.short_name(name)
            v.full_name = self.full_name(name, parent_name)

            v.initializer = enumvalue_element.findtext("initializer", "")
            v.brief, v.description = _select_descriptions(
                self.parse_description(enumvalue_element.find("briefdescription")),
                self.parse_description(enumvalue_element.find("detaileddescription")))

            values.append(v)
            self._parser.register(v)

        return values

    def parse_member(self, memberdef_element: ET.Element, parent: Compound) -> Optional[Member]:
        member = Member(self.TAG)
        member.id = self.unique_id(memberdef_element.get("id"))
        member.kind = memberdef_element.get("kind", "")
        member.prot = memberdef_element.get("prot", "")

        name = self.cleanup_name(memberdef_element.findtext("name", ""))
        member.name = self.short_name(name)
        member.full_name = self.full_name(name, parent.full_name)
        member.namespace = self.namespace(member.full_name)

        if self.is_member_blacklisted(member.kind, member.name):
            return None

        member.definition = memberdef_element.findtext("definition", "")
        member.args = memberdef_element.findtext("argsstring", "")
        member.params = self.parse_parameters(memberdef_element, member)
        member.exceptions = self.parse_exceptions(memberdef_element, member)
        member.brief, member.description = _select_descriptions(
            self.parse_description(memberdef_element.find("briefdescription")),
            self.parse_description(memberdef_element.find("detaileddescription")))
        member.returns = self.parse_returns(memberdef_element, member)
        member.enumvalues = self.parse_enumvalues(memberdef_element, member.full_name)
        member.static = _yes_no_to_bool(memberdef_element.get("static", "false"))

        self._parser.register(member)
        return member

    def parse_innerclass(self, parent: Compound, parent_compound: ET.Element) \
            -> List[InnerTypeReference]:
        inner_classes = []

        for xml_inner_class in parent_compound.iterfind("innerclass"):
            type_visibility = xml_inner_class.get("prot")
            if type_visibility not in ("public", "protected", None):
                continue

            inner_type = InnerTypeReference(parent.language)
            inner_type.id = self.unique_id(xml_inner_class.get("refid"))
            inner_type.name = \
                self.cleanup_name(xml_inner_class.text if xml_inner_class.text else "")
            inner_type.namespace = parent.full_name

            inner_classes.append(inner_type)
            self._parser.unresolved_ref(inner_type)

        return inner_classes

    def parse_compounddef(self, compounddef_element: ET.Element) -> None:
        compound = Compound(self.TAG)
        compound.id = self.unique_id(compounddef_element.get("id"))
        compound.kind = compounddef_element.get("kind", "")

        name = self.cleanup_name(compounddef_element.findtext("compoundname", ""))
        compound.name = self.short_name(name)
        compound.full_name = self.full_name(name)
        compound.namespace = self.namespace(compound.full_name)

        compound.members = [
            member
            for member in (self.parse_member(memberdef, compound)
                           for memberdef in compounddef_element.iterfind("sectiondef/memberdef"))
            if member is not None
        ]
        compound.inner_classes = self.parse_innerclass(compound, compounddef_element)

        compound.brief, compound.description = _select_descriptions(
            self.parse_description(compounddef_element.find("briefdescription")),
            self.parse_description(compounddef_element.find("detaileddescription")))
        compound.enumvalues = self.parse_enumvalues(compounddef_element, compound.full_name)
        compound.include = compounddef_element.findtext("includes")

        self._parser.register(compound)

    def unique_id(self, id: Optional[str]) -> Optional[str]:
        if not id:
            return None

        # Workaround a bug in asciidoctor: if there is an occurrence of __ the anchor is not parsed
        # correctly: #2746
        id = id.replace("__", "-")

        return f"{self.TAG}-{id}"

    def cleanup_name(self, name: str) -> str:
        return name

    def short_name(self, name: str) -> str:
        return name

    def full_name(self, name: str, parent: str = "") -> str:
        return name

    def namespace(self, full_name: str) -> Optional[str]:
        return None

    def is_member_blacklisted(self, kind: str, name: str) -> bool:
        return False


class CppLanguage(Language):
    """Language support for C++."""
    TAG: str = "cpp"

    TYPE_PREFIXES = re.compile(r"((const|volatile|constexpr|mutable|enum|class)\s*)+\s+")
    TYPE_SUFFIXES = re.compile(r"(\s*(\*|&|const))+")
    TYPE_NESTED_START = re.compile(r"\s*<\s*")
    TYPE_NESTED_SEPARATOR = re.compile(r"\s*,\s*")
    TYPE_NESTED_END = re.compile(r"\s*>")
    TYPE_NAME = re.compile(r"((unsigned|signed|short|long)\s+)*(?:(?!\bconst)[a-zA-Z0-9_:])+")

    LANGUAGE_BUILD_IN_TYPES = ("void", "bool", "signed char", "unsigned char", "char", "wchar_t",
                               "char16_t", "char32_t", "char8_t", "float", "double", "long double",
                               "short", "short int", "signed short", "signed short int",
                               "unsigned short", "unsigned short int", "int", "signed",
                               "signed int", "unsigned", "unsigned int", "long", "long int",
                               "signed long", "signed long int", "unsigned long",
                               "unsigned long int", "long long", "long long int",
                               "signed long long", "signed long long int", "unsigned long long",
                               "unsigned long long int")

    def is_language_standard_type(self, type_name: str) -> bool:
        return type_name in self.LANGUAGE_BUILD_IN_TYPES or type_name.startswith("std::")

    def short_name(self, name: str) -> str:
        return name.split("::")[-1]

    def full_name(self, name: str, parent: str = "") -> str:
        if name.startswith(parent):
            return name
        return f"{parent}::{name}"

    def namespace(self, full_name: str) -> Optional[str]:
        if "::" in full_name:
            namespace, _ = full_name.rsplit("::", maxsplit=1)
            return namespace
        else:
            return None

    def is_member_blacklisted(self, kind: str, name: str) -> bool:
        return kind == "friend"


class JavaLanguage(Language):
    """Language support for Java."""
    TAG: str = "java"

    TYPE_PREFIXES = re.compile(r"((([\w?]+?\s+extends)|final|synchronized|transient)\s*)+\s+")
    TYPE_SUFFIXES = re.compile(r"")
    TYPE_NESTED_START = re.compile(r"\s*<\s*")
    TYPE_NESTED_SEPARATOR = re.compile(r"\s*,\s*")
    TYPE_NESTED_END = re.compile(r"\s*>")
    TYPE_NAME = re.compile(r"[a-zA-Z0-9_:\.? ]+")

    LANGUAGE_BUILD_IN_TYPES = ("void", "long", "int", "boolean", "byte", "char", "short", "float",
                               "double", "String")
    COMMON_GENERIC_NAMES = ("T", "?", "T ", "? ")

    def is_language_standard_type(self, type_name: str) -> bool:
        return (type_name in self.LANGUAGE_BUILD_IN_TYPES or type_name in self.COMMON_GENERIC_NAMES
                or type_name.startswith("java.") or type_name.startswith("android.")
                or type_name.startswith("native "))

    def cleanup_name(self, name: str) -> str:
        return name.replace("::", ".").strip()

    def short_name(self, name: str) -> str:
        return name.split(".")[-1]

    def full_name(self, name: str, parent: str = "") -> str:
        if name.startswith(parent):
            return name
        return f"{parent}.{name}"

    def namespace(self, full_name: str) -> Optional[str]:
        if "." in full_name:
            namespace, _ = full_name.rsplit(".", maxsplit=1)
            return namespace
        else:
            return None


class ObjectiveCLanguage(Language):
    """Language support for Objective C."""
    TAG: str = "objc"

    TYPE_PREFIXES = re.compile(r"((nullable|const|__weak|__strong)\s*)+\s+")
    TYPE_SUFFIXES = re.compile(r"(\s*\*\s*?)+")
    TYPE_NESTED_START = re.compile(r"\s*<\s*")
    TYPE_NESTED_SEPARATOR = re.compile(r"\s*,\s*")
    TYPE_NESTED_END = re.compile(r"\s*>")
    TYPE_NAME = re.compile(r"((unsigned|signed|short|long)\s+)*[a-zA-Z0-9_:]+")

    BLOCK = re.compile(r"typedef (.+)\(\^(.+)\)\s*\((.*)\)")

    LANGUAGE_BUILD_IN_TYPES = ("char", "unsigned char", "signed char", "int", "unsigned int",
                               "short", "unsigned short", "long", "unsigned long", "float",
                               "double", "long double", "void", "bool", "BOOL", "id",
                               "instancetype")

    def is_language_standard_type(self, type_name: str) -> bool:
        return type_name in self.LANGUAGE_BUILD_IN_TYPES or type_name.startswith("NS")

    def cleanup_name(self, name: str) -> str:
        if name.endswith("-p"):
            return name[:-2]
        return name

    def full_name(self, name: str, parent: str = "") -> str:
        if name.startswith(parent):
            return name
        if parent.endswith(".h"):
            # Parent is a header file, do not prepend
            return name
        return f"{parent}.{name}"

    def parse_member(self, memberdef_element: ET.Element, parent: Compound) -> Optional[Member]:
        member = super().parse_member(memberdef_element, parent)
        if member is None:
            return None

        if member.kind in ("variable", "typedef") and "^" in member.definition:
            self._redefine_as_block(member, parent)

        return member

    def _redefine_as_block(self, member: Member, parent: Compound) -> None:
        block_match = self.BLOCK.search(member.definition)
        if not block_match:
            return

        return_type = block_match.group(1)
        name = block_match.group(2).strip()
        args = block_match.group(3).strip()

        member.kind = "block"
        member.name = name

        def type_from_text(text):
            type_element = ET.Element("type")
            type_element.text = text
            return self.parse_type(type_element, member)

        member.returns = ReturnValue()
        member.returns.type = type_from_text(return_type)

        if args:
            for arg in args.split(","):
                param = Parameter()
                param.type = type_from_text(arg.strip())
                member.params.append(param)

    def namespace(self, full_name: str) -> Optional[str]:
        if "." in full_name:
            namespace, _ = full_name.rsplit(".", maxsplit=1)
            return namespace
        else:
            return None

    def is_member_blacklisted(self, kind: str, name: str) -> bool:
        return kind == "function" and name == "NS_ENUM"


class DoxygenXmlParser(object):
    """Parser for Doxygen XML output."""
    api_reference: ApiReference
    _unresolved_refs: List[TypeRefBase]
    _force_language: Optional[str]

    _languages: Mapping[str, Language]

    def __init__(self, force_language: Optional[str] = None):
        self.api_reference = ApiReference()
        self._unresolved_refs = []
        self._force_language = safe_language_tag(force_language)

        self._languages = {
            CppLanguage.TAG: CppLanguage(self),
            JavaLanguage.TAG: JavaLanguage(self),
            ObjectiveCLanguage.TAG: ObjectiveCLanguage(self),
        }

        if not self._force_language:
            self._force_language = None
        elif self._force_language not in self._languages:
            logger.error(f"Unknown forced language: {self._force_language}. Falling back to auto"
                         " detection.")
            self._force_language = None

    def _parse_element(self, xml_element: ET.Element) -> None:
        if self._force_language is not None:
            language_tag = self._force_language
        else:
            language_tag = safe_language_tag(xml_element.get("language"))
            if not language_tag:
                return
            if language_tag not in self._languages:
                logger.debug(f"Unknown language: {language_tag}")
                return

        if xml_element.tag == "compounddef":
            self._languages[language_tag].parse_compounddef(xml_element)
        else:
            logger.debug(f"Unhandled element: {xml_element.tag}")

    def parse(self, file_or_path) -> bool:
        """Parse all objects in an XML file and make them available for API reference generation.

        Params:
            file_or_path: File object or path for the XML file to parse.

        Returns:
            True if file is parsed. False if the file is invalid.
        """

        tree = ET.parse(file_or_path)
        root = tree.getroot()
        if root.tag != "doxygen":
            return False

        for e in root:
            self._parse_element(e)
        return True

    def register(self, element: ReferableElement) -> None:
        self.api_reference.elements.append(element)

    def unresolved_ref(self, ref: TypeRefBase) -> None:
        self._unresolved_refs.append(ref)

    def resolve_references(self) -> None:
        """Resolve all references between objects from different XML files."""

        unresolved_names: Set[str] = set()
        still_unresolved = []
        for ref in self._unresolved_refs:
            assert ref.name

            # Try perfect match
            try:
                class_match = self.api_reference.find(ref.name,
                                                      target_id=ref.id,
                                                      lang=ref.language,
                                                      namespace=ref.namespace)
                if class_match is not None:
                    ref.resolve(class_match)
                    continue
            except AmbiguousLookupError:
                pass

            # Find partial matches in namespaces or other scopes
            matches = []
            for compound in self.api_reference.elements:
                if compound.name and compound.full_name.endswith(f"::{ref.name}"):
                    matches.append(compound)
            if len(matches) == 1:
                ref.resolve(matches[0])
                continue
            elif len(matches) > 1:
                logger.debug(f"Multiple matches: {ref.name} ")

            still_unresolved.append(ref)
            unresolved_names.add(ref.name)

        logger.debug(f"Resolved refs: {len(self._unresolved_refs) - len(still_unresolved)}")
        logger.debug(f"Still unresolved: {len(still_unresolved)}: {', '.join(unresolved_names)}")
        self._unresolved_refs = still_unresolved


def safe_language_tag(name: Optional[str]) -> str:
    """Convert language names to tags that are safe to use for identifiers and file names.

    Args:
        name: Name to convert to a safe name. Can be `None`.

    Returns:
        A safe string to use for identifiers and file names.
    """
    if name is None:
        return ""

    name = name.lower()
    return {"c++": "cpp", "objective-c": "objc"}.get(name, name)
