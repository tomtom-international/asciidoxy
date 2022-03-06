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
"""Errors raised by different parts of the generator."""

from typing import List, Optional

from .._version import __version__
from ..api_reference import normalized_type_str
from ..document import Document
from ..model import Compound, ReferableElement


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
            if isinstance(element, Compound) and element.kind == "function":
                signature = f"({', '.join(normalized_type_str(e.type) for e in element.params)})"

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


class InvalidApiCallError(AsciiDocError):
    """The API call is invalid in the current context, or the arguments given are invalid.

    Args:
        msg: Message explaining what is wrong with the call.
    """
    msg: str

    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self) -> str:
        return f"Invalid API call: {self.msg}"


class MissingPackageError(AsciiDocError):
    """The specified package is missing from the package specification.

    Args:
        package_name: Name of the missing package.
    """
    package_name: str

    def __init__(self, package_name: str):
        self.package_name = package_name

    def __str__(self) -> str:
        return f"The package `{self.package_name}` is not available."


class MissingPackageFileError(AsciiDocError):
    """The specified file is missing from the package.

    Args:
        package_name: Name of the missing package.
        file_name:    Name of the missing file.
    """
    package_name: str
    file_name: Optional[str]

    def __init__(self, package_name: str, file_name: Optional[str]):
        self.package_name = package_name
        self.file_name = file_name

    def __str__(self) -> str:
        if self.file_name:
            return (f"Package `{self.package_name}` does not contain file `{self.file_name}`.")
        else:
            return (f"Package `{self.package_name}` does not specify a root document.")


class DuplicateAnchorError(AsciiDocError):
    """An anchor with the the same name already exists.

    Args:
        anchor_name: Name of the anchor.
    """
    anchor_name: str

    def __init__(self, anchor_name: str):
        self.anchor_name = anchor_name

    def __str__(self) -> str:
        return f"Anchor with name `{self.anchor_name}` inserted multiple times."


class UnknownAnchorError(AsciiDocError):
    """The refered anchor does not exist in any included document.

    Args:
        anchor_name: Name of the anchor.
    """
    anchor_name: str

    def __init__(self, anchor_name: str):
        self.anchor_name = anchor_name

    def __str__(self) -> str:
        return f"Anchor with name `{self.anchor_name}` does not exist."


class DuplicateIncludeError(AsciiDocError):
    """A file has been included multiple times or has been both included and embedded.

    Args:
        document: The offending document.
        embedded: Is the file also embedded.
    """
    document: Document
    embedded: bool

    def __init__(self, document: Document, embedded: bool):
        self.document = document
        self.embedded = embedded

    def __str__(self) -> str:
        if self.embedded:
            return (f"{self.document} has been both included and embedded."
                    " This can lead to unexpected results with links and TOCs.")
        else:
            return (f"{self.document} has been included multiple times."
                    " This can lead to unexpected results with links and TOCs.")
