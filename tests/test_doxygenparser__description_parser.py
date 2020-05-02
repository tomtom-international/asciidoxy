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
"""
Tests for the Doxygen XML description parser.
"""

import pytest
import re

import xml.etree.ElementTree as ET

from asciidoxy.doxygenparser.description_parser import DescriptionParser
from tests.shared import sub_element


def nested_formatting():
    entries = []

    entries.append(([], ""))

    element = ET.Element("para")
    element.text = "Another paragraph"
    result = "Another paragraph\n\n"
    entries.append(([element], result))

    element = ET.Element("bold")
    element.text = "Bold text"
    result = "**Bold text**"
    entries.append(([element], result))

    element = ET.Element("highlight")
    element.text = "Highlighted"
    result = "__Highlighted__"
    entries.append(([element], result))

    element1 = ET.Element("bold")
    element1.text = "Bold text"
    element2 = ET.Element("highlight")
    element2.text = "Highlighted"
    result = "**Bold text**__Highlighted__"
    entries.append(([element1, element2], result))

    return entries


def test_text_only():
    description = ET.Element("description", text="A text only description")
    result = DescriptionParser("lang").parse(description)
    assert result == ""


def test_single_para():
    description = ET.Element("description")
    sub_element(description, "para", text="Actual description text.")
    result = DescriptionParser("lang").parse(description)
    assert result == f"Actual description text."


def test_multiple_para():
    description = ET.Element("description")
    sub_element(description, "para", text="Actual description text.")
    sub_element(description, "para", text="And some more text.")
    result = DescriptionParser("lang").parse(description)
    assert result == """Actual description text.

And some more text."""


def test_nested_para():
    description = ET.Element("description")
    sub_element(description, "para", text="Outer text.")
    sub_element(description, "para", text="Inner text.", tail="Tail outer text.")
    result = DescriptionParser("lang").parse(description)
    assert result == """Outer text.

Inner text.

Tail outer text."""


@pytest.mark.parametrize("nested_elements, nested_result", nested_formatting())
def test_itemizedlist(nested_elements, nested_result):
    description = ET.Element("description")
    para = sub_element(description, "para", text="This is a list of items:")
    itemized_list = sub_element(para, "itemizedlist", tail="And some text after the list")

    list_item_1 = sub_element(itemized_list, "listitem")
    para_1 = sub_element(list_item_1, "para", text="List item 1")
    para_1.extend(nested_elements)

    list_item_2 = sub_element(itemized_list, "listitem")
    sub_element(list_item_2, "para", text="List item 2")

    result = DescriptionParser("lang").parse(description)
    assert result == re.sub(
        "\n{3,}", "\n\n", f"""This is a list of items:

* List item 1{nested_result}

* List item 2

And some text after the list""")


@pytest.mark.parametrize("nested_elements, nested_result", nested_formatting())
def test_bold(nested_elements, nested_result):
    description = ET.Element("description")
    para = sub_element(description, "para", text="The following is ")
    bold = sub_element(para, "bold", text="very, very, very", tail=" important!")
    bold.extend(nested_elements)

    result = DescriptionParser("lang").parse(description)
    assert result == f"The following is **very, very, very{nested_result}** important!"


@pytest.mark.parametrize("nested_elements, nested_result", nested_formatting())
def test_highlight(nested_elements, nested_result):
    description = ET.Element("description")
    para = sub_element(description, "para", text="I want to ")
    highlight = sub_element(para, "highlight", text="highlight these words", tail=" properly.")
    highlight.extend(nested_elements)

    result = DescriptionParser("lang").parse(description)
    assert result == f"I want to __highlight these words{nested_result}__ properly."


def test_computeroutput():
    description = ET.Element("description")
    para = sub_element(description, "para", text="The computer says: ")
    sub_element(para, "computeroutput", text="I cannot do that, Dave", tail="!")

    result = DescriptionParser("lang").parse(description)
    assert result == "The computer says: `I cannot do that, Dave`!"


def test_programlisting():
    description = ET.Element("description")
    para = sub_element(description, "para", text="Example of code:")
    listing = sub_element(para, "programlisting", tail="You know what it does.")
    sub_element(listing, "codeline", text="def main():")
    sub_element(listing, "codeline", text="    print('Hello world!')")
    sub_element(listing, "codeline")

    result = DescriptionParser("lang").parse(description)
    assert result == """Example of code:
[source,lang]
----
def main():
    print('Hello world!')

----
You know what it does."""


@pytest.mark.parametrize("nested_elements, nested_result", nested_formatting())
def test_ulink(nested_elements, nested_result):
    description = ET.Element("description")
    para = sub_element(description, "para", text="Follow ")
    link = sub_element(para,
                       "ulink",
                       text="this link",
                       tail=" for more information.",
                       url="https://www.tomtom.com")
    link.extend(nested_elements)

    result = DescriptionParser("lang").parse(description)
    assert (
        result == f"Follow https://www.tomtom.com[this link{nested_result}] for more information.")


@pytest.mark.parametrize("nested_elements, nested_result", nested_formatting())
def test_ref(nested_elements, nested_result):
    description = ET.Element("description")
    para = sub_element(description, "para", text="See ")
    link = sub_element(para,
                       "ref",
                       text="Class",
                       tail=" for more information.",
                       refid="compound_class")
    link.extend(nested_elements)

    result = DescriptionParser("lang").parse(description)
    assert result == f"See xref:lang-compound_class[Class{nested_result}] for more information."


def test_ignore_parameterlist():
    description = ET.Element("description")
    para = sub_element(description, "para")
    parameterlist = sub_element(para, "parameterlist", text="Ignored", tail="Also ignored")
    sub_element(parameterlist, "para", text="Ignored", tail="Ignored as well")

    result = DescriptionParser("lang").parse(description)
    assert result == ""


@pytest.mark.parametrize("kind", ["note", "tip", "important", "caution", "warning"])
def test_simplesect_supported_kind(kind):
    description = ET.Element("description")
    para = sub_element(description, "para", "Some normal text first.")
    simplesect = sub_element(para, "simplesect", kind=kind, tail="More text after the note.")
    sub_element(simplesect, "para", text="Some kind of note.")

    result = DescriptionParser("lang").parse(description)
    assert result == f"""Some normal text first.
[{kind.upper()}]
====
Some kind of note.

====
More text after the note."""


@pytest.mark.parametrize("kind", ["return", "unknown"])
def test_simplesect_ignore_other_kinds(kind):
    description = ET.Element("description")
    para = sub_element(description, "para", "Some normal text first.")
    simplesect = sub_element(para, "simplesect", kind=kind, tail="More text after the note.")
    sub_element(simplesect, "para", text="Some kind of note.")

    result = DescriptionParser("lang").parse(description)
    assert result == "Some normal text first."


@pytest.mark.parametrize("nested_elements, nested_result", nested_formatting())
def test_unknown_tag(nested_elements, nested_result):
    description = ET.Element("description")
    para = sub_element(description, "para", text="The following is ")
    unknown = sub_element(para, "unknown", text="very, very, very", tail=" important!")
    unknown.extend(nested_elements)

    result = DescriptionParser("lang").parse(description)
    assert result == re.sub("\n ", "\n",
                            f"The following is very, very, very{nested_result} important!")


def test_remove_trailing_whitespace():
    description = ET.Element("description")
    sub_element(description, "para", text="Actual description text.")
    sub_element(description, "para", text="And some more text.", tail="   \n   ")
    result = DescriptionParser("lang").parse(description)
    assert result == """Actual description text.

And some more text."""


def test_remove_single_leading_space():
    description = ET.Element("description")
    sub_element(description, "para", text=" Actual description text.")
    sub_element(description, "para", text=" And some more text.")
    result = DescriptionParser("lang").parse(description)
    assert result == """Actual description text.

And some more text."""
