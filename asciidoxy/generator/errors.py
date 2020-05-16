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
"""Errors raised by different parts of the generator."""

from typing import List, Optional

from ..model import Member, ReferableElement
from .._version import __version__


class AsciiDocError(Exception):
    """Base class for errors while processing an AsciiDoc input file."""
    pass


class TemplateMissingError(AsciiDocError):
    """There is no template to render a specific element.

    Attributes:
        lang: Language of the element missing a template.
        kind: Kind of element missing a template
    """
    lang: str
    kind: str

    def __init__(self, lang: str, kind: str):
        self.lang = lang
        self.kind = kind

    def __str__(self) -> str:
        return f"There is no template to render a {self.kind} for {self.lang}"


class ReferenceNotFoundError(AsciiDocError):
    """The reference specified in the document cannot be found.

    Attributes:
        name: Name in the reference.
        lang: Language specified in the reference.
        kind: Element kind specified in the reference.
    """
    name: str
    lang: str
    kind: str

    def __init__(self, name: str, lang: Optional[str], kind: Optional[str]):
        self.lang = lang or "any"
        self.kind = kind or "any"
        self.name = name

    def __str__(self) -> str:
        return f"Cannot find {self.kind} {self.name} for {self.lang}"


class UnlinkableError(AsciiDocError):
    """The reference cannot be linked to.

    Attributes:
        name: Name in the reference.
        lang: Language specified in the reference.
        kind: Element kind specified in the reference.
    """
    name: str
    lang: str
    kind: str

    def __init__(self, name: str, lang: Optional[str], kind: Optional[str]):
        self.lang = lang or "any"
        self.kind = kind or "any"
        self.name = name

    def __str__(self) -> str:
        return (f"Cannot link to {self.kind} {self.name} for {self.lang}."
                " This may be a bug/limitation in AsciiDoxy or missing information in the Doxygen"
                " XML files.")


class AmbiguousReferenceError(AsciiDocError):
    """The reference matches multiple elements.

    Attributes:
        name: Name in the reference.
        candidates: All candidates that match the search query.
    """
    name: str
    candidates: List[ReferableElement]

    def __init__(self, name: str, candidates: List[ReferableElement]):
        self.name = name
        self.candidates = candidates

    def __str__(self) -> str:
        def element_to_str(element: ReferableElement) -> str:
            signature = ""
            if isinstance(element, Member) and element.kind == "function":
                signature = f"({', '.join(str(e.type) for e in element.params)})"

            return f"{element.language} {element.kind} {element.full_name}{signature}"

        return (f"Multiple matches for {self.name}. Please provide more details."
                "\nMatching candidates:\n" + "\n".join(element_to_str(e) for e in self.candidates))


class IncludeFileNotFoundError(AsciiDocError):
    """Include file cannot be found on the file system.

    Attributes:
        file_name: Name of the file that cannot be found.
    """
    file_name: str

    def __init__(self, file_name: str):
        self.file_name = file_name

    def __str__(self) -> str:
        return f"Include file not found: {self.file_name}"


class ConsistencyError(AsciiDocError):
    """There is an inconsistency in the generated documentation.

    E.g. links are dangling.

    Attributes:
        msg: Message explaining the inconsistency.
    """
    msg: str

    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class IncompatibleVersionError(AsciiDocError):
    """The running version of AsciiDoxy is not compatible with the input file.

    """
    required_version: str

    def __init__(self, required_version: str):
        self.required_version = required_version

    def __str__(self) -> str:
        return (f"Input file requires version {self.required_version} of AsciiDoxy. "
                f"Current version {__version__} is not compatible.")
