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
"""Parse brief and detailed descriptions from Doxygen XML."""

import logging
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Iterator, List, Mapping, Optional, Tuple, Type, TypeVar, Union

logger = logging.getLogger(__name__)


def parse_description(xml_root: Optional[ET.Element], language_tag: str) -> "ParaContainer":
    """Parse a description from Doxygen XML.

    Expects either `briefdescription` or `detaileddescription`. In case of `detaileddescription` it
    can contain additional sections documenting parameters and return types.

    Args:
        xml_root: Element to start processing from.
        language_tag: Tag indicating the programming language.
    Returns:
        A container with description paragraphs and sections.
    """
    try:
        contents = ParaContainer(language_tag)
        if xml_root is not None:
            for xml_element in xml_root:
                _parse_description(xml_element, contents, language_tag)
            contents.normalize()
        return contents
    except AssertionError:
        if xml_root is not None:
            ET.dump(xml_root)
        raise


def select_descriptions(brief: "ParaContainer", detailed: "ParaContainer") -> Tuple[str, str]:
    """Select the approprate brief and detailed descriptions.

    Sometimes one of the descriptions is missing. This method makes sure there is always at least
    a brief description.

    Args:
        brief: Brief description as found in the XML.
        detailed: Detailed description as found in the XML.

    Returns:
        brief: Brief description to use.
        detailed: Detailed description to use.
    """
    brief_adoc = brief.to_asciidoc()
    if brief_adoc:
        return brief_adoc, detailed.to_asciidoc()

    if detailed.contents:
        brief.contents.append(detailed.contents.pop(0))
    return brief.to_asciidoc(), detailed.to_asciidoc()


###################################################################################################
# Core elements and interfaces
###################################################################################################


class AsciiDocContext:
    """Context for generating AsciiDoc.

    Some elements are context-aware. They need to adapt to the elements they are nested in.
    """
    def __init__(self):
        self.table_separators = []
        self.list_markers = []


class DescriptionElement(ABC):
    """A description in Doxygen XML is made up of several different XML elements. Each element
    requires its own conversion into AsciiDoc format.
    """
    language_tag: str

    def __init__(self, language_tag: str):
        self.language_tag = language_tag

    @abstractmethod
    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        """Convert the element, and all contained elements, to AsciiDoc format."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "DescriptionElement":
        """Generate a description element from its XML counterpart.

        Information and attributes from XML can be used, but the contained text and the tail text
        are handled separately.
        """
        return cls(language_tag)

    def update_from_xml(self, xml_element: ET.Element):
        """Update the current element with information from another XML element.

        By default this method does nothing. To be implemented only by subclasses that support or
        require information from some if its children, without adding a new element for the child.
        """

    def add_text(self, text: str) -> None:
        """Add the text inside the XML element.

        By default the text is ignored. To be implemented only by subclasses that use the text.
        """

    def add_tail(self, parent: "NestedDescriptionElement", text: str) -> None:
        """Add the text after the closing tag of the element.

        By default the tail is ignored. To be used by subclasses that support tail text. The parent
        can be used to create additional elements for the tail text after the current element.
        """


class NestedDescriptionElement(DescriptionElement):
    """A description element that contains additional description elements.

    Attributes:
        contents: Additional description elements inside this element.
    """
    contents: List[DescriptionElement]

    def __init__(self, language_tag: str, *contents: DescriptionElement):
        super().__init__(language_tag)
        self.contents = list(contents)

    def append(self, content: DescriptionElement) -> None:
        if content:
            self.contents.append(content)

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return "".join(element.to_asciidoc(context) for element in self.contents)

    def normalize(self) -> None:
        for child in self.children_of_type(NestedDescriptionElement):
            child.normalize()

    ChildT = TypeVar("ChildT", bound="DescriptionElement")

    def children_of_type(self, child_type: Type[ChildT]) -> Iterator[ChildT]:
        return (child for child in self.contents if isinstance(child, child_type))

    def first_child_of_type(self, child_type: Type[ChildT]) -> Optional[ChildT]:
        return next(self.children_of_type(child_type), None)


class NamedSection:
    """Special paragraph indicating a section that can be retrieved by name.

    Attributes:
        name: Name of the section.
    """
    name: str

    def __init__(self, name: str = ""):
        self.name = name


###################################################################################################
# Simple elements without nested content
###################################################################################################


class PlainText(DescriptionElement):
    """Plain text.

    Formatting may be applied by parent elements.

    Attributes:
        text: The plain text.
    """
    text: str

    def __init__(self, language_tag: str, text: str = ""):
        super().__init__(language_tag)
        self.text = text

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return self.text.strip("\r\n")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {repr(self.text)}"

    def add_text(self, text: str) -> None:
        self.text += text


class Formula(DescriptionElement):
    """Formula in LatexMath format.

    Attributes:
        text: Contents of the formula.
    """
    text: str

    def __init__(self, language_tag: str, text: str = ""):
        super().__init__(language_tag)
        self.text = text

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        stripped_text = self.text.strip("\r\n")
        if stripped_text.startswith(r"\[") and stripped_text.endswith(r"\]"):
            stripped_text = stripped_text[3:-3].strip()
        return f"latexmath:[{stripped_text}]"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {repr(self.text)}"

    def add_text(self, text: str) -> None:
        self.text += text

    def add_tail(self, parent: NestedDescriptionElement, text: str):
        parent.append(PlainText(self.language_tag, text))


class Image(DescriptionElement):
    """Insert an image.

    Attributes:
        output_type: Output document type the image is meant for. For now we only support `html`.
        file_name:   Name if the image file. Must be available in the images of the package.
        alt_text:    Alternative text when the image cannot be loaded, or for accessibility.
        width:       Optional width to show the image with.
        height:      Optional height to show the image with.
        inline:      Yes if the image needs to be inlined in the text.
    """
    output_type: str
    file_name: str
    alt_text: str
    width: str
    height: str
    inline: str

    def __init__(self, language_tag: str, output_type: str, file_name: str, width: str, height: str,
                 inline: str):
        super().__init__(language_tag)
        self.output_type = output_type
        self.file_name = file_name
        self.alt_text = ""
        self.width = width
        self.height = height
        self.inline = inline

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        if self.output_type != "html":
            return ""

        if self.width or self.height:
            options = f'"{self.alt_text}",{self.width},{self.height}'
        elif self.alt_text:
            options = f'"{self.alt_text}"'
        else:
            options = ""

        if self.inline == "yes":
            separator = ":"
        else:
            separator = "::"

        return f"image{separator}{self.file_name}[{options}]"

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}: {self.output_type}->{self.file_name}, "
                f"{repr(self.alt_text)}, width={self.width}, height={self.height}, "
                f"inline={self.inline}")

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Image":
        return cls(language_tag, xml_element.get("type", ""), xml_element.get("name", ""),
                   xml_element.get("width", ""), xml_element.get("height", ""),
                   xml_element.get("inline", "no"))

    def add_text(self, text: str) -> None:
        self.alt_text += text

    def add_tail(self, parent: NestedDescriptionElement, text: str):
        parent.append(PlainText(self.language_tag, text))


class SpecialCharacter(PlainText):
    """Special character represented by an XML tag.

    Attributes:
        tag: Original XML tag.
    """
    tag: str

    SPECIAL_CHARACTERS = {
        "sp": " ",
        "linebreak": " +\n",
        "nonbreakablespace": "&nbsp;",
        "iexcl": "",
        "cent": "",
        "pound": "",
        "curren": "",
        "yen": "",
        "brvbar": "",
        "sect": "",
        "umlaut": "",
        "copy": "",
        "ordf": "",
        "laquo": "",
        "not": "",
        "shy": "",
        "registered": "",
        "macr": "",
        "deg": "",
        "plusmn": "",
        "sup2": "",
        "sup3": "",
        "acute": "",
        "micro": "",
        "middot": "",
        "cedil": "",
        "sup1": "",
        "ordm": "",
        "raquo": "",
        "frac14": "",
        "frac12": "",
        "frac34": "",
        "iquest": "",
        "Agrave": "",
        "Aacute": "",
        "Acirc": "",
        "Atilde": "",
        "Aumlaut": "",
        "Aring": "",
        "AElig": "",
        "Ccedil": "",
        "Egrave": "",
        "Eacute": "",
        "Ecirc": "",
        "Eumlaut": "",
        "Igrave": "",
        "Iacute": "",
        "Icirc": "",
        "Iumlaut": "",
        "ETH": "",
        "Ntilde": "",
        "Ograve": "",
        "Oacute": "",
        "Ocirc": "",
        "Otilde": "",
        "Oumlaut": "",
        "times": "",
        "Oslash": "",
        "Ugrave": "",
        "Uacute": "",
        "Ucirc": "",
        "Uumlaut": "",
        "Yacute": "",
        "THORN": "",
        "szlig": "",
        "agrave": "",
        "aacute": "",
        "acirc": "",
        "atilde": "",
        "aumlaut": "",
        "aring": "",
        "aelig": "",
        "ccedil": "",
        "egrave": "",
        "eacute": "",
        "ecirc": "",
        "eumlaut": "",
        "igrave": "",
        "iacute": "",
        "icirc": "",
        "iumlaut": "",
        "eth": "",
        "ntilde": "",
        "ograve": "",
        "oacute": "",
        "ocirc": "",
        "otilde": "",
        "oumlaut": "",
        "divide": "",
        "oslash": "",
        "ugrave": "",
        "uacute": "",
        "ucirc": "",
        "uumlaut": "",
        "yacute": "",
        "thorn": "",
        "yumlaut": "",
        "fnof": "",
        "Alpha": "",
        "Beta": "",
        "Gamma": "",
        "Delta": "",
        "Epsilon": "",
        "Zeta": "",
        "Eta": "",
        "Theta": "",
        "Iota": "",
        "Kappa": "",
        "Lambda": "",
        "Mu": "",
        "Nu": "",
        "Xi": "",
        "Omicron": "",
        "Pi": "",
        "Rho": "",
        "Sigma": "",
        "Tau": "",
        "Upsilon": "",
        "Phi": "",
        "Chi": "",
        "Psi": "",
        "Omega": "",
        "alpha": "",
        "beta": "",
        "gamma": "",
        "delta": "",
        "epsilon": "",
        "zeta": "",
        "eta": "",
        "theta": "",
        "iota": "",
        "kappa": "",
        "lambda": "",
        "mu": "",
        "nu": "",
        "xi": "",
        "omicron": "",
        "pi": "",
        "rho": "",
        "sigmaf": "",
        "sigma": "",
        "tau": "",
        "upsilon": "",
        "phi": "",
        "chi": "",
        "psi": "",
        "omega": "",
        "thetasym": "",
        "upsih": "",
        "piv": "",
        "bull": "",
        "hellip": "",
        "prime": "",
        "Prime": "",
        "oline": "",
        "frasl": "",
        "weierp": "",
        "imaginary": "",
        "real": "",
        "trademark": "",
        "alefsym": "",
        "larr": "",
        "uarr": "",
        "rarr": "",
        "darr": "",
        "harr": "",
        "crarr": "",
        "lArr": "",
        "uArr": "",
        "rArr": "",
        "dArr": "",
        "hArr": "",
        "forall": "",
        "part": "",
        "exist": "",
        "empty": "",
        "nabla": "",
        "isin": "",
        "notin": "",
        "ni": "",
        "prod": "",
        "sum": "",
        "minus": "",
        "lowast": "",
        "radic": "",
        "prop": "",
        "infin": "",
        "ang": "",
        "and": "",
        "or": "",
        "cap": "",
        "cup": "",
        "int": "",
        "there4": "",
        "sim": "",
        "cong": "",
        "asymp": "",
        "ne": "",
        "equiv": "",
        "le": "",
        "ge": "",
        "sub": "",
        "sup": "",
        "nsub": "",
        "sube": "",
        "supe": "",
        "oplus": "",
        "otimes": "",
        "perp": "",
        "sdot": "",
        "lceil": "",
        "rceil": "",
        "lfloor": "",
        "rfloor": "",
        "lang": "",
        "rang": "",
        "loz": "",
        "spades": "",
        "clubs": "",
        "hearts": "",
        "diams": "",
        "OElig": "",
        "oelig": "",
        "Scaron": "",
        "scaron": "",
        "Yumlaut": "",
        "circ": "",
        "tilde": "",
        "ensp": "",
        "emsp": "",
        "thinsp": "",
        "zwnj": "",
        "zwj": "",
        "lrm": "",
        "rlm": "",
        "ndash": "",
        "mdash": "",
        "lsquo": "",
        "rsquo": "",
        "sbquo": "",
        "ldquo": "",
        "rdquo": "",
        "bdquo": "",
        "dagger": "",
        "Dagger": "",
        "permil": "",
        "lsaquo": "",
        "rsaquo": "",
        "euro": "",
        "tm": "",
    }

    def __init__(self, language_tag: str, text: str = "", tag: str = ""):
        super().__init__(language_tag, text)
        self.tag = tag

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        adoc_repr = self.SPECIAL_CHARACTERS.get(self.tag, "")
        if not adoc_repr:
            adoc_repr = f"&{self.tag};"
        return f"{adoc_repr}{super().to_asciidoc()}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.tag} {self.text}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "SpecialCharacter":
        return cls(language_tag, tag=xml_element.tag)

    def add_tail(self, parent: NestedDescriptionElement, text: str):
        self.text += text


class Emoji(PlainText):
    """A Unicode emoji."""
    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Emoji":
        return cls(language_tag, text=xml_element.get("unicode", ""))

    def add_tail(self, parent: NestedDescriptionElement, text: str):
        self.text += text


###################################################################################################
# Paragraphs and collections of paragraphs
###################################################################################################


class ParaContainer(NestedDescriptionElement):
    """Element that contains a sequence of paragraphes."""
    def append(self, content: DescriptionElement) -> None:
        assert isinstance(content, (Para, ParaContainer))
        super().append(content)

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return "\n\n".join(
            element.to_asciidoc(context) for element in self.contents
            if element.to_asciidoc(context).strip())

    def normalize(self) -> None:
        new_contents: List[DescriptionElement] = []
        while self.contents:
            child = self.contents.pop(0)

            # Normalize ParaContainers and add them if not empty
            if isinstance(child, (Para, ParaContainer)):
                child.normalize()

            if isinstance(child, ParaContainer):
                child.normalize()
                if child.contents:
                    new_contents.append(child)
                continue

            assert isinstance(child, Para)

            # Paras and ParaContainers inside a Para need to be promoted to the current
            # ParaContainer. Split the existing content in separate Paras around other Paras and
            # ParaContainers

            # Clone the original Para for the initial non-Para content
            new_para = child.clone_without_contents()
            while child.contents and not isinstance(child.contents[0], (Para, ParaContainer)):
                new_para.append(child.contents.pop(0))
            new_contents.append(new_para)

            reassess = []
            while child.contents:
                # Promote Paras and ParaContainers
                while child.contents and isinstance(child.contents[0], (Para, ParaContainer)):
                    reassess.append(child.contents.pop(0))

                # Use the last Para to reasses, or clone the original Para for following non-Para
                # content
                if isinstance(reassess[-1], Para):
                    new_para = reassess.pop(-1)
                else:
                    new_para = child.clone_without_contents()
                while child.contents and not isinstance(child.contents[0], (Para, ParaContainer)):
                    new_para.append(child.contents.pop(0))
                reassess.append(new_para)
            self.contents = reassess + self.contents

        self.contents = new_contents

    SectionT = TypeVar("SectionT", bound="NamedSection")

    def pop_section(self, section_type: Type[SectionT], name: str) -> Optional[SectionT]:
        queue: List[NestedDescriptionElement] = [self]
        while queue:
            current = queue.pop(0)
            for i, child in enumerate(current.contents):
                if isinstance(child, section_type) and child.name == name:
                    return current.contents.pop(i)
                elif isinstance(child, NestedDescriptionElement):
                    queue.append(child)
        return None


class Para(NestedDescriptionElement):
    """A single paragraph of text."""
    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return super().to_asciidoc(context).strip()

    def clone_without_contents(self):
        return self.__class__(self.language_tag)

    def add_text(self, text: str) -> None:
        self.append(PlainText(self.language_tag, text))


class Section(ParaContainer):
    """Collection of paragraphs with a title or header.

    Attributes:
        title: Title of the section. Shown as a discrete header before the paragraphs.
        level: Level of the header used for the section.
    """
    title: str
    level: int

    def __init__(self,
                 language_tag: str,
                 title: str = "",
                 level: int = 1,
                 *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.title = title
        self.level = level

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        header = f"[discrete]\n{'=' * self.level} {self.title}"
        return f"{header}\n\n{super().to_asciidoc(context)}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: level={self.level}, {repr(self.title)}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Section":
        level = int(xml_element.tag[4:])
        return cls(language_tag=language_tag, level=level)

    def update_from_xml(self, xml_element: ET.Element):
        if xml_element.tag == "title":
            assert xml_element.text
            self.title = xml_element.text.strip()


class Heading(Para):
    """Heading where the nested content is the heading itself.

    Attributes:
        level: Level of the heading.
    """
    level: int

    def __init__(self, language_tag: str, level: int = 1, *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.level = level

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return f"[discrete]\n{'=' * self.level} {super().to_asciidoc(context)}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: level={self.level}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Heading":
        return cls(language_tag=language_tag, level=int(xml_element.get("level", "1")))

    def clone_without_contents(self):
        return self.__class__(self.language_tag, level=self.level)


class Admonition(ParaContainer, NamedSection):
    """Special paragraph indicating a text section that is either an admonition or sidebar."""
    ADMONITION_MAP = {
        "ATTENTION": "CAUTION",
        "NOTE": "NOTE",
        "REMARK": "NOTE",
        "WARNING": "WARNING",
    }

    def __init__(self, language_tag: str, name: str = "", *contents: DescriptionElement):
        ParaContainer.__init__(self, language_tag, *contents)
        NamedSection.__init__(self, name)

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        admonition = self.ADMONITION_MAP.get(self.name.upper())
        if admonition is None:
            return f".{self.name.capitalize()}\n[NOTE]\n====\n{super().to_asciidoc(context)}\n===="
        else:
            return f"[{admonition}]\n====\n{super().to_asciidoc(context)}\n===="

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Admonition":
        return cls(language_tag=language_tag, name=xml_element.get("kind", "").lower())

    def update_from_xml(self, xml_element: ET.Element):
        if xml_element.tag in ("xreftitle", "title"):
            assert xml_element.text
            self.name = xml_element.text.lower()

    def add_tail(self, parent: NestedDescriptionElement, text: str):
        parent.append(Para(self.language_tag, PlainText(self.language_tag, text.lstrip())))


class Verbatim(Para):
    """Piece of text to show verbatim.

    Args:
        text: Text to show.
    """
    text: str

    def __init__(self, language_tag: str, text: str = ""):
        super().__init__(language_tag)
        self.text = text

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        stripped_text = self.text.strip("\r\n")
        return f"----\n{stripped_text}\n----"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {repr(self.text)}"

    def clone_without_contents(self) -> "Verbatim":
        return self.__class__(self.language_tag, self.text)

    def add_text(self, text: str) -> None:
        self.text += text


class Diagram(Para):
    """Textual description of a diagram that can be used to generate a picture.

    Attributes:
        generator: The generator required to create the diagram.
    """
    GENERATOR_MAP = {
        "dot": "graphviz",
    }
    generator: str

    def __init__(self, language_tag: str, generator: str, *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.generator = generator

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        # Not using Para.to_asciidoc() due to extra stripping that needs to be avoided here
        generator = self.GENERATOR_MAP.get(self.generator, self.generator)
        return f"[{generator}]\n....\n{NestedDescriptionElement.to_asciidoc(self, context)}\n...."

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.generator}"

    def clone_without_contents(self) -> "Diagram":
        return self.__class__(self.language_tag, self.generator)

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Diagram":
        return cls(language_tag, xml_element.tag)

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        parent.append(Para(self.language_tag, PlainText(self.language_tag, text.lstrip())))


class BlockQuote(ParaContainer):
    """One or more paragraphs forming a quote."""
    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return f"[quote]\n____\n{super().to_asciidoc(context)}\n____"


class HorizontalRuler(Para):
    """Horizontal ruler."""
    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return "'''"


class Center(Para):
    """Center a paragraph of text."""
    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return f"[.text-center]\n{super().to_asciidoc(context)}"


class ParBlock(ParaContainer):
    """One or more paragraphs that form a block together.

    This differs from a normal ParaContainer as `+` is used to make sure paragraphs remain together
    in blocks like definitions or lists.
    """
    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return "\n+\n".join(
            element.to_asciidoc(context) for element in self.contents
            if element.to_asciidoc(context).strip())


###################################################################################################
# Formatting
###################################################################################################


class Style(NestedDescriptionElement):
    """Apply a text style to contained elements.

    Attributes:
        kind: The kind of style to apply.
    """
    STYLE_MAP = {
        "emphasis": ("__", "__"),
        "bold": ("**", "**"),
        "computeroutput": ("``", "``"),
        "strike": ("[.line-through]#", "#"),
        "subscript": ("~", "~"),
        "underline": ("[.underline]#", "#"),
        "small": ("[.small]#", "#"),
        "superscript": ("^", "^"),
        "ins": ("+++<ins>+++", "+++</ins>+++"),
        "del": ("+++<del>+++", "+++</del>+++"),
        "s": ("[.line-through]#", "#"),
    }

    kind: str

    def __init__(self, language_tag: str, kind: str, *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.kind = kind

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        style_start, style_end = self.STYLE_MAP.get(self.kind, ("", ""))
        return f"{style_start}{super().to_asciidoc(context)}{style_end}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.kind}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Style":
        return cls(language_tag=language_tag, kind=xml_element.tag)

    def add_text(self, text: str) -> None:
        self.append(PlainText(self.language_tag, text))

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        parent.append(PlainText(self.language_tag, text))


class Ref(NestedDescriptionElement):
    """Reference to an API element. This appears as a hyperlink.

    Attributes:
        refid: Unique identifier of the API element.
        kindref: The kind of API element referred to.
    """
    refid: str
    kindref: str

    def __init__(self, language_tag: str, refid: str, kindref: str, *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.refid = refid
        self.kindref = kindref

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return f"<<{self.language_tag}-{self.refid},{super().to_asciidoc(context)}>>"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.kindref}[{self.refid}]"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Ref":
        return cls(language_tag, xml_element.get("refid", ""), xml_element.get("kindref", ""))

    def add_text(self, text: str) -> None:
        self.append(PlainText(self.language_tag, text))

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        parent.append(PlainText(self.language_tag, text))


class Ulink(NestedDescriptionElement):
    """Link to an external URL. This appears as a hyperlink.

    All nested elements will be part of the link.

    Attributes:
        url: URL to link to.

    """
    url: str

    def __init__(self, language_tag: str, url: str, *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.url = url

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return f"{self.url}[{super().to_asciidoc(context)}]"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.url}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Ulink":
        return cls(language_tag, xml_element.get("url", ""))

    def add_text(self, text: str) -> None:
        self.append(PlainText(self.language_tag, text))

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        parent.append(PlainText(self.language_tag, text))


class Anchor(PlainText):
    """Anchor that can be referenced in hyperlinks.

    Attributes:
        id: Identifier of the anchor.
    """
    id: str

    def __init__(self, language_tag: str, text: str = "", id: str = ""):
        super().__init__(language_tag, text)
        self.id = id

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return f"[#{self.language_tag}-{self.id}]\n{super().to_asciidoc().lstrip()}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.id} {repr(self.text)}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Anchor":
        return cls(language_tag, id=xml_element.get("id", ""))

    def add_tail(self, parent: NestedDescriptionElement, text: str):
        self.text += text


###################################################################################################
# Tables
###################################################################################################


class Table(NestedDescriptionElement):
    """A table.

    Attributes:
        caption:   Optional caption for the table.
        cols:      The number of columns in the table.
    """
    caption: Optional[str]
    cols: str

    def __init__(self,
                 language_tag: str,
                 caption: Optional[str] = None,
                 cols: str = "1",
                 *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.caption = caption
        self.cols = cols

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        context = context or AsciiDocContext()

        if len(context.table_separators) == 0:
            separator = "|"
        elif len(context.table_separators) > 0:
            separator = "!"
            if len(context.table_separators) > 1:
                logger.warning("Table nesting is only supported one level deep.")

        context.table_separators.append(separator)
        rows = "\n\n".join(element.to_asciidoc(context) for element in self.contents)
        context.table_separators.pop(-1)

        if self.caption:
            caption = f".{self.caption}\n"
        else:
            caption = ""

        options = f"[cols=\"{self.cols}*\", options=\"autowidth\"]"

        return f"{caption}{options}\n{separator}===\n\n{rows}\n\n{separator}==="

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: cols={self.cols}, {self.caption}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Table":
        return cls(language_tag, cols=xml_element.get("cols", "1"))

    def update_from_xml(self, xml_element: ET.Element) -> None:
        if xml_element.tag == "caption":
            self.caption = xml_element.text


class Row(NestedDescriptionElement):
    """A single row in a table."""
    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return "\n".join(element.to_asciidoc(context) for element in self.contents)


class Entry(ParaContainer):
    """A single cell/entry in a table.

    Attributes:
        header:    Is this cell part of a header.
        rowspan:   The number of rows the cell spans. Not specified means 1.
        colspan:   The number of columns the cell spans. Not specified means 1.
    """
    header: Optional[str]
    rowspan: Optional[str]
    colspan: Optional[str]
    align: Optional[str]

    def __init__(self,
                 language_tag: str,
                 header: Optional[str] = None,
                 rowspan: Optional[str] = None,
                 colspan: Optional[str] = None,
                 align: Optional[str] = None,
                 *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.header = header
        self.rowspan = rowspan
        self.colspan = colspan
        self.align = align

    def add_text(self, text: str) -> None:
        """Ignore text outside paras."""

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        """Ignore text outside paras."""

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        assert context is not None
        assert context.table_separators
        separator = context.table_separators[-1]

        if self.header == "yes":
            style_operator = "h"
        else:
            style_operator = "a"

        if self.rowspan and self.colspan:
            span_operator = f"{self.colspan}.{self.rowspan}+"
        elif self.rowspan:
            span_operator = f".{self.rowspan}+"
        elif self.colspan:
            span_operator = f"{self.colspan}+"
        else:
            span_operator = ""

        align_operator = {"left": "", "center": "^", "right": ">", None: ""}.get(self.align, "")

        return (f"{span_operator}{align_operator}{style_operator}{separator} "
                f"{super().to_asciidoc(context)}")

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}: header={self.header}, rowspan={self.rowspan}, "
                f"colspan={self.colspan}, align={self.align}")

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "Entry":
        return cls(language_tag, xml_element.get("thead", None), xml_element.get("rowspan", None),
                   xml_element.get("colspan", None), xml_element.get("align", None))


###################################################################################################
# Lists
###################################################################################################


class ListContainer(ParaContainer):
    """Paragraph that contains a list (bullet or ordered).

    Attributes:
        marker: Marker used for each list item.
    """

    marker: str

    def __init__(self, language_tag: str, marker: str, *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.marker = marker

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        context = context or AsciiDocContext()

        if context.list_markers:
            if context.list_markers[-1].startswith(self.marker):
                marker = f"{context.list_markers[-1]}{self.marker}"
            else:
                marker = self.marker
        else:
            marker = self.marker

        context.list_markers.append(marker)
        ret = super().to_asciidoc(context)
        context.list_markers.pop(-1)

        return ret

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "ListContainer":
        if xml_element.tag == "orderedlist":
            marker = "."
        else:
            marker = "*"

        return cls(language_tag=language_tag, marker=marker)

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        parent.append(Para(self.language_tag, PlainText(self.language_tag, text.lstrip())))


class ListItem(ParaContainer):
    """A single item in a bullet list.

    The item itself can contain multiple paragraphs.
    """
    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        assert context is not None
        assert context.list_markers
        marker = context.list_markers[-1]
        return f"{marker} {super().to_asciidoc(context)}"

    def add_text(self, text: str) -> None:
        """Ignore text outside paras."""

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        """Ignore text outside paras."""


###################################################################################################
# Code blocks
###################################################################################################


class ProgramListing(Para):
    """A block of code."""
    EXTENSION_MAPPING = {
        "py": "python",
        "kt": "kotlin",
        "mm": "objc",
        "unparsed": "",
    }

    filename: str

    def __init__(self, language_tag: str, filename: str, *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.filename = filename

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        code = "\n".join(element.to_asciidoc(context) for element in self.contents)

        if self.filename:
            _, _, extension = self.filename.partition(".")
            language = self.EXTENSION_MAPPING.get(extension, extension)
        else:
            language = self.language_tag
        return f"[source,{language}]\n----\n{code}\n----"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "ProgramListing":
        return cls(language_tag, xml_element.get("filename", ""))

    def clone_without_contents(self):
        return self.__class__(self.language_tag, self.filename)

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        parent.append(Para(self.language_tag, PlainText(self.language_tag, text.lstrip())))


class CodeLine(NestedDescriptionElement):
    """A single line in a block of code."""


###################################################################################################
# Parameter description lists
###################################################################################################


class ParameterList(NestedDescriptionElement, NamedSection):
    """Special section containing a list of parameter descriptions."""
    def __init__(self, language_tag: str, name: str, *contents: NestedDescriptionElement):
        NestedDescriptionElement.__init__(self, language_tag, *contents)
        NamedSection.__init__(self, name)

    def to_asciidoc(self, context: AsciiDocContext = None) -> str:
        return ""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "ParameterList":
        return cls(language_tag, xml_element.get("kind", ""))


class ParameterItem(NestedDescriptionElement):
    """Combination of name, type and description of a parameter."""
    def first_name(self) -> Optional["ParameterName"]:
        return self.first_child_of_type(ParameterName)

    def names(self) -> Iterator["ParameterName"]:
        return self.children_of_type(ParameterName)

    def description(self) -> Optional["ParameterDescription"]:
        return self.first_child_of_type(ParameterDescription)


class ParameterName(NestedDescriptionElement):
    """Name or type of a single parameter.

    Some parameters only have a name, while others can contain references to types.

    Attributes:
        name: Name of the parameter.
        direction: If supported, whether this is an in-parameter, out-parameter, or both.
    """
    name: Optional[str]
    direction: Optional[str]

    def __init__(self, language_tag: str, name=None, direction=None, *contents: DescriptionElement):
        super().__init__(language_tag, *contents)
        self.name = name
        self.direction = direction

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.name or ''} [{self.direction or ''}]"

    @classmethod
    def from_xml(cls, xml_element: ET.Element, language_tag: str) -> "ParameterName":
        return cls(language_tag, direction=xml_element.get("direction", None))

    def add_text(self, text: str) -> None:
        self.name = text


class ParameterDescription(ParaContainer):
    """Description of a single parameter."""


###################################################################################################
# Special functionality
###################################################################################################


class Skipped(PlainText):
    """An item that is skipped, either because it must be ignored or because it is not supported."""
    def add_text(self, text: str) -> None:
        """Ignored."""


# Map of element tags for which a new element is to be constructed and added the the parent.
NEW_ELEMENT: Mapping[str, Type[DescriptionElement]] = {
    "anchor": Anchor,
    "blockquote": BlockQuote,
    "bold": Style,
    "center": Center,
    "codeline": CodeLine,
    "computeroutput": Style,
    "del": Style,
    "dot": Diagram,
    "emoji": Emoji,
    "emphasis": Style,
    "entry": Entry,
    "formula": Formula,
    "heading": Heading,
    "highlight": Style,
    "hruler": HorizontalRuler,
    "image": Image,
    "ins": Style,
    "itemizedlist": ListContainer,
    "listitem": ListItem,
    "orderedlist": ListContainer,
    "para": Para,
    "parameterdescription": ParameterDescription,
    "parameteritem": ParameterItem,
    "parameterlist": ParameterList,
    "parametername": ParameterName,
    "parblock": ParBlock,
    "plantuml": Diagram,
    "preformatted": Verbatim,
    "programlisting": ProgramListing,
    "ref": Ref,
    "row": Row,
    "s": Style,
    "sect1": Section,
    "sect2": Section,
    "sect3": Section,
    "sect4": Section,
    "sect5": Section,
    "sect6": Section,
    "sect7": Section,
    "sect8": Section,
    "sect9": Section,
    "simplesect": Admonition,
    "small": Style,
    "strike": Style,
    "subscript": Style,
    "superscript": Style,
    "table": Table,
    "ulink": Ulink,
    "underline": Style,
    "verbatim": Verbatim,
    "xrefsect": Admonition,
}

# Map of element tags that update the parent element.
UPDATE_PARENT: Mapping[str, Union[Type, Tuple[Type, ...]]] = {
    "caption": Table,
    "title": (Admonition, Section),
    "xreftitle": Admonition,
}

# Map of element tags for which the children update its parent.
USE_PARENT = {
    "parameternamelist": ParameterItem,
    "xrefdescription": Admonition,
    "htmlonly": object,
    "xmlonly": object,
}

# Element tags to ignore, including their nested content.
IGNORE = {
    "docbookonly",
    "manonly",
    "rtfonly",
    "latexonly",
    "internal",
}

# Tags known to be unsupported for now. If a text is present, it is shown to the user as a warning,
# otherwise it is silently ignored.
UNSUPPORTED = {
    # Using dotfile generates an absolute path in the XML. AsciiDoxy cannot resolve that.
    "dotfile":
    "External dot files are not supported. Use inline dot diagrams instead.",

    # Index entries
    "secondaryie":
    "",
    "indexentry":
    "",
    "primaryie":
    "",

    # TOC
    "tocitem":
    "",
    "toclist":
    "",

    # Diagram types not supported by AsciiDoctor Diagram
    "msc":
    "MSC diagrams are not supported by AsciiDoctor.",
    "mscfile":
    "MSC diagrams are not supported by AsciiDoctor.",
    "diafile":
    "Dia files are not supported by AsciiDoctor.",

    # Multiple language support
    "language": ("Multiple languages are not supported by AsciiDoxy yet. Language specific text "
                 "will be missing from the generated documentation."),

    # Other
    "variablelist":
    "Please report an issue on GitHub with example code.",
    "parametertype":
    "Please report an issue on GitHub with example code.",

    # Not seen when using @copydoc. Content is already duplicated in the XML output.
    "copydoc":
    "Please report an issue on GitHub with example code.",
}


def _parse_description(xml_element: ET.Element, parent: NestedDescriptionElement,
                       language_tag: str):
    element = None

    if xml_element.tag in NEW_ELEMENT:
        element = NEW_ELEMENT[xml_element.tag].from_xml(xml_element, language_tag)

    elif xml_element.tag in UPDATE_PARENT:
        assert isinstance(parent, UPDATE_PARENT[xml_element.tag])
        parent.update_from_xml(xml_element)
        element = parent

    elif xml_element.tag in USE_PARENT:
        assert isinstance(parent, USE_PARENT[xml_element.tag])
        element = parent

    elif xml_element.tag in SpecialCharacter.SPECIAL_CHARACTERS:
        element = SpecialCharacter.from_xml(xml_element, language_tag)

    elif xml_element.tag in IGNORE:
        element = Skipped.from_xml(xml_element, language_tag)

    elif xml_element.tag in UNSUPPORTED:
        warning = UNSUPPORTED[xml_element.tag]
        if warning:
            logger.warning(f"Unsupported XML tag <{xml_element.tag}>. {warning}")
        element = Skipped.from_xml(xml_element, language_tag)

    else:
        logger.warning(f"Unknown XML tag <{xml_element.tag}>. Please report an issue on GitHub"
                       " with example code.")

    if element is None:
        return
    if element is not parent:
        parent.append(element)

    if xml_element.text:
        element.add_text(xml_element.text)

    if xml_element.tail:
        element.add_tail(parent, xml_element.tail)

    if isinstance(element, NestedDescriptionElement):
        for child in xml_element:
            _parse_description(child, element, language_tag)
