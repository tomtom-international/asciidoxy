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
"""Test parsing brief and detailed descriptions from Doxygen XML."""

import xml.etree.ElementTree as ET

from asciidoxy.parser.doxygen.description_parser import (
    Admonition,
    DescriptionElement,
    NestedDescriptionElement,
    ParameterList,
    Ref,
    SpecialCharacter,
    parse_description,
    select_descriptions,
)


def debug_print(element: DescriptionElement, prefix: str = "") -> None:
    print(f"{prefix}{repr(element)}")
    if isinstance(element, NestedDescriptionElement):
        for child in element.contents:
            debug_print(child, f"{prefix}  ")


def parse(input_xml):
    output = parse_description(ET.fromstring(input_xml), "lang")
    debug_print(output)
    return output


def test_parse_styles():
    input_xml = """\
        <detaileddescription>
<para>Description with all kinds of Doxygen styles.</para>
<para>Several <emphasis>words</emphasis> in this <emphasis>sentence</emphasis> are <emphasis>italic</emphasis>.</para>
<para>Several <bold>words</bold> in this <bold>sentence</bold> are <bold>bold</bold>.</para>
<para>Also a <computeroutput>some</computeroutput> words in <computeroutput>monotype</computeroutput>. </para>
        </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Description with all kinds of Doxygen styles.

Several __words__ in this __sentence__ are __italic__.

Several **words** in this **sentence** are **bold**.

Also a ``some`` words in ``monotype``."""


def test_parse_lists():
    input_xml = """\
    <detaileddescription>
<para>Description with some Doxygen lists.</para>
<para><itemizedlist>
<listitem><para><computeroutput>AlignLeft</computeroutput> left alignment. </para>
</listitem>
<listitem><para><computeroutput>AlignCenter</computeroutput> center alignment. </para>
</listitem>
<listitem><para><computeroutput>AlignRight</computeroutput> right alignment</para>
</listitem>
</itemizedlist>
Another list:</para>
<para><itemizedlist>
<listitem><para><bold>Bold</bold>. </para>
</listitem>
<listitem><para><emphasis>Italic</emphasis>. </para>
</listitem>
<listitem><para><computeroutput>Monotype</computeroutput>. </para>
</listitem>
</itemizedlist>
</para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Description with some Doxygen lists.

* ``AlignLeft`` left alignment.

* ``AlignCenter`` center alignment.

* ``AlignRight`` right alignment

Another list:

* **Bold**.

* __Italic__.

* ``Monotype``."""


def test_parse_code_blocks():
    input_xml = """\
    <detaileddescription>
<para>Description with some code blocks.</para>
<para>Python example:</para>
<para><programlisting filename=".py"><codeline><highlight class="normal">class<sp/>Python:</highlight></codeline>
<codeline><highlight class="normal"><sp/><sp/><sp/><sp/></highlight><highlight class="keywordflow">pass</highlight></codeline>
</programlisting></para>
<para>C++ example:</para>
<para><programlisting filename=".cpp"><codeline><highlight class="keyword">class<sp/></highlight><highlight class="normal">Cpp<sp/>{};</highlight></codeline>
</programlisting></para>
<para>Unparsed code:</para>
<para><programlisting filename=".unparsed"><codeline><highlight class="normal">Show<sp/>this<sp/>as-is<sp/>please</highlight></codeline>
</programlisting></para>
<para>Using the default language, C++ in this case:</para>
<para><programlisting><codeline><highlight class="normal">class<sp/>AlsoCpp<sp/>{};</highlight></codeline>
</programlisting></para>
<para>That&apos;s all folks! </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Description with some code blocks.

Python example:

[source,python]
----
class Python:
    pass
----

C++ example:

[source,cpp]
----
class Cpp {};
----

Unparsed code:

[source,]
----
Show this as-is please
----

Using the default language, C++ in this case:

[source,lang]
----
class AlsoCpp {};
----

That's all folks!"""


def test_parse_diagrams():
    input_xml = """\
    <detaileddescription>
<para>Description with several diagrams.</para>
<para>Class relations expressed via an inline dot graph: <dot>
digraph example {
    node [shape=record, fontname=Helvetica, fontsize=10];
    b [ label=&quot;class B&quot; URL=&quot;\ref DoxygenList&quot;];
    c [ label=&quot;class C&quot; URL=&quot;\ref CodeBlock&quot;];
    b -&gt; c [ arrowhead=&quot;open&quot;, style=&quot;dashed&quot; ];
}
</dot>
 Note that the classes in the above graph are clickable (in the HTML output).</para>
<para>Receiver class. Can be used to receive and execute commands. After execution of a command, the receiver will send an acknowledgment <plantuml>  Receiver&lt;-Sender  : Command()
  Receiver--&gt;Sender : Ack()</plantuml>
 </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Description with several diagrams.

Class relations expressed via an inline dot graph:

[graphviz]
....
digraph example {
    node [shape=record, fontname=Helvetica, fontsize=10];
    b [ label="class B" URL="
ef DoxygenList"];
    c [ label="class C" URL="
ef CodeBlock"];
    b -> c [ arrowhead="open", style="dashed" ];
}
....

Note that the classes in the above graph are clickable (in the HTML output).

Receiver class. Can be used to receive and execute commands. After execution of a command, the receiver will send an acknowledgment

[plantuml]
....
  Receiver<-Sender  : Command()
  Receiver-->Sender : Ack()
...."""


def test_parse_sections():
    input_xml = """\
    <detaileddescription>
<para>This class demonstrates how all sections supported by Doxygen are handled. <simplesect kind="author"><para>Rob van der Most </para>
</simplesect>
<simplesect kind="attention"><para>Be carefull with this class. It <bold>could</bold> blow up. </para>
</simplesect>
<xrefsect id="bug_1_bug000001"><xreftitle>Bug</xreftitle><xrefdescription><para>Not all sections may be rendered correctly. </para>
</xrefdescription></xrefsect><simplesect kind="copyright"><para>MIT license. </para>
</simplesect>
<simplesect kind="date"><para>28 August 2021 </para>
</simplesect>
<xrefsect id="deprecated_1_deprecated000001"><xreftitle>Deprecated</xreftitle><xrefdescription><para>This empty class should no longer be used. </para>
</xrefdescription></xrefsect><simplesect kind="note"><para>Don&apos;t forget about <computeroutput>this!</computeroutput> </para>
</simplesect>
<simplesect kind="pre"><para>The class should not exist yet. </para>
</simplesect>
<simplesect kind="post"><para>The class suddenly exists. </para>
</simplesect>
<simplesect kind="remark"><para>This class does not make much sense. </para>
</simplesect>
<simplesect kind="since"><para>0.7.6 </para>
</simplesect>
<xrefsect id="todo_1_todo000001"><xreftitle>Todo</xreftitle><xrefdescription><para>Create some content here. </para>
</xrefdescription></xrefsect><simplesect kind="warning"><para>Do not use this class ever! </para>
</simplesect>
</para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
This class demonstrates how all sections supported by Doxygen are handled.

.Author
[NOTE]
====
Rob van der Most
====

[CAUTION]
====
Be carefull with this class. It **could** blow up.
====

.Bug
[NOTE]
====
Not all sections may be rendered correctly.
====

.Copyright
[NOTE]
====
MIT license.
====

.Date
[NOTE]
====
28 August 2021
====

.Deprecated
[NOTE]
====
This empty class should no longer be used.
====

[NOTE]
====
Don't forget about ``this!``
====

.Pre
[NOTE]
====
The class should not exist yet.
====

.Post
[NOTE]
====
The class suddenly exists.
====

[NOTE]
====
This class does not make much sense.
====

.Since
[NOTE]
====
0.7.6
====

.Todo
[NOTE]
====
Create some content here.
====

[WARNING]
====
Do not use this class ever!
===="""


def test_parse_function():
    input_xml = """\
        <detaileddescription>
<para>Complete documentation for a function or method.</para>
<para><parameterlist kind="param"><parameteritem>
<parameternamelist>
<parametername direction="in">first</parametername>
</parameternamelist>
<parameterdescription>
<para>The first parameter. </para>
</parameterdescription>
</parameteritem>
<parameteritem>
<parameternamelist>
<parametername direction="out">second</parametername>
</parameternamelist>
<parameterdescription>
<para>The second parameter. </para>
</parameterdescription>
</parameteritem>
<parameteritem>
<parameternamelist>
<parametername direction="inout">third</parametername>
</parameternamelist>
<parameterdescription>
<para>The third parameter. </para>
</parameterdescription>
</parameteritem>
</parameterlist>
<simplesect kind="return"><para>A status code </para>
</simplesect>
<parameterlist kind="retval"><parameteritem>
<parameternamelist>
<parametername>0</parametername>
</parameternamelist>
<parameterdescription>
<para>All is ok. </para>
</parameterdescription>
</parameteritem>
<parameteritem>
<parameternamelist>
<parametername>1</parametername>
</parameternamelist>
<parameterdescription>
<para>Something went wrong. </para>
</parameterdescription>
</parameteritem>
</parameterlist>
<parameterlist kind="exception"><parameteritem>
<parameternamelist>
<parametername>std::logic_error</parametername>
</parameternamelist>
<parameterdescription>
<para>Something is wrong with the logic. </para>
</parameterdescription>
</parameteritem>
</parameterlist>
<parameterlist kind="templateparam"><parameteritem>
<parameternamelist>
<parametername>Type</parametername>
</parameternamelist>
<parameterdescription>
<para>The type to do something with. </para>
</parameterdescription>
</parameteritem>
</parameterlist>
</para>
        </detaileddescription>
"""
    output = parse(input_xml)

    templateparam_section = output.pop_section(ParameterList, "templateparam")
    assert templateparam_section is not None
    assert templateparam_section.name == "templateparam"
    assert len(templateparam_section.contents) == 1
    assert len(list(templateparam_section.contents[0].names())) == 1
    name = templateparam_section.contents[0].first_name()
    assert name.name == "Type"
    assert not name.direction
    description = templateparam_section.contents[0].description()
    assert description is not None
    assert description.to_asciidoc() == "The type to do something with."

    exception_section = output.pop_section(ParameterList, "exception")
    assert exception_section is not None
    assert exception_section.name == "exception"
    assert len(exception_section.contents) == 1
    assert len(list(exception_section.contents[0].names())) == 1
    name = exception_section.contents[0].first_name()
    assert name.name == "std::logic_error"
    assert not name.direction
    description = exception_section.contents[0].description()
    assert description.to_asciidoc() == "Something is wrong with the logic."

    retval_section = output.pop_section(ParameterList, "retval")
    assert retval_section is not None
    assert retval_section.name == "retval"
    assert len(retval_section.contents) == 2
    assert len(list(retval_section.contents[0].names())) == 1
    name = retval_section.contents[0].first_name()
    assert name.name == "0"
    assert not name.direction
    description = retval_section.contents[0].description()
    assert description is not None
    assert description.to_asciidoc() == "All is ok."
    assert len(list(retval_section.contents[1].names())) == 1
    name = retval_section.contents[1].first_name()
    assert name.name == "1"
    assert not name.direction
    description = retval_section.contents[1].description()
    assert description.to_asciidoc() == "Something went wrong."

    return_section = output.pop_section(Admonition, "return")
    assert return_section is not None
    assert return_section.name == "return"
    assert len(return_section.contents) == 1
    assert return_section.contents[0].to_asciidoc() == "A status code"

    param_section = output.pop_section(ParameterList, "param")
    assert param_section is not None
    assert param_section.name == "param"
    assert len(param_section.contents) == 3
    assert len(list(param_section.contents[0].names())) == 1
    name = param_section.contents[0].first_name()
    assert name.name == "first"
    assert name.direction == "in"
    description = param_section.contents[0].description()
    assert description is not None
    assert description.to_asciidoc() == "The first parameter."
    assert len(list(param_section.contents[1].names())) == 1
    name = param_section.contents[1].first_name()
    assert name.name == "second"
    assert name.direction == "out"
    description = param_section.contents[1].description()
    assert description is not None
    assert description.to_asciidoc() == "The second parameter."
    assert len(list(param_section.contents[2].names())) == 1
    name = param_section.contents[2].first_name()
    assert name.name == "third"
    assert name.direction == "inout"
    description = param_section.contents[2].description()
    assert description is not None
    assert description.to_asciidoc() == "The third parameter."

    assert output.to_asciidoc() == """\
Complete documentation for a function or method."""


def test_parse_links():
    input_xml = """\
    <detaileddescription>
<para><ref refid="classasciidoxy_1_1descriptions_1_1_links" kindref="compound">Links</ref> to other elements.</para>
<para>Some other test classes are: <itemizedlist>
<listitem><para><ref refid="classasciidoxy_1_1descriptions_1_1_code_block" kindref="compound">CodeBlock</ref> for code blocks. </para>
</listitem>
<listitem><para><ref refid="classasciidoxy_1_1descriptions_1_1_diagrams" kindref="compound">Diagrams</ref> for plantUML and Dot. </para>
</listitem>
<listitem><para><ref refid="classasciidoxy_1_1descriptions_1_1_sections" kindref="compound">Sections</ref> for all kinds of sections.</para>
</listitem>
</itemizedlist>
Of course there is also <ref refid="descriptions_8hpp_1ac2b05985028362b43839a108f8b30a24" kindref="member">FunctionDocumentation()</ref>. </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
<<lang-classasciidoxy_1_1descriptions_1_1_links,Links>> to other elements.

Some other test classes are:

* <<lang-classasciidoxy_1_1descriptions_1_1_code_block,CodeBlock>> for code blocks.

* <<lang-classasciidoxy_1_1descriptions_1_1_diagrams,Diagrams>> for plantUML and Dot.

* <<lang-classasciidoxy_1_1descriptions_1_1_sections,Sections>> for all kinds of sections.

Of course there is also <<lang-descriptions_8hpp_1ac2b05985028362b43839a108f8b30a24,FunctionDocumentation()>>."""


def test_parse_external_links():
    input_xml = """\
    <detaileddescription>
<para>Our website is <ulink url="https://asciidoxy.org">https://asciidoxy.org</ulink>. You can use <ulink url="mailto:info@example.com">info@example.com</ulink> for fake e-mail address examples.</para>
<para>Don&apos;t forget to read our <ulink url="https://asciidoxy.org">documentation</ulink>. </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Our website is https://asciidoxy.org[https://asciidoxy.org]. You can use mailto:info@example.com[info@example.com] for fake e-mail address examples.

Don't forget to read our https://asciidoxy.org[documentation]."""


def test_parse_complex_html_table():
    input_xml = """\
    <detaileddescription>
<para><table rows="9" cols="3"><caption>Complex table</caption>
<row>
<entry thead="yes"><para>Column 1 </para>
</entry><entry thead="yes"><para>Column 2 </para>
</entry><entry thead="yes"><para>Column 3 </para>
</entry></row>
<row>
<entry thead="no" rowspan="2"><para>cell row=1+2,col=1</para>
</entry><entry thead="no"><para>cell row=1,col=2</para>
</entry><entry thead="no"><para>cell row=1,col=3 </para>
</entry></row>
<row>
<entry thead="no" rowspan="2"><para>cell row=2+3,col=2 </para>
</entry><entry thead="no"><para>cell row=2,col=3 </para>
</entry></row>
<row>
<entry thead="no"><para>cell row=3,col=1 </para>
</entry><entry thead="no" rowspan="2"><para>cell row=3+4,col=3 </para>
</entry></row>
<row>
<entry thead="no" colspan="2"><para>cell row=4,col=1+2 </para>
</entry></row>
<row>
<entry thead="no"><para>cell row=5,col=1 </para>
</entry><entry thead="no" colspan="2"><para>cell row=5,col=2+3 </para>
</entry></row>
<row>
<entry thead="no" colspan="2" rowspan="2"><para>cell row=6+7,col=1+2 </para>
</entry><entry thead="no"><para>cell row=6,col=3 </para>
</entry></row>
<row>
<entry thead="no"><para>cell row=7,col=3 </para>
</entry></row>
<row>
<entry thead="no"><para>cell row=8,col=1 </para>
</entry><entry thead="no"><para>cell row=8,col=2<linebreak/>
<table rows="2" cols="2"><row>
<entry thead="no"><para>Inner cell row=1,col=1</para>
</entry><entry thead="no"><para>Inner cell row=1,col=2 </para>
</entry></row>
<row>
<entry thead="no"><para>Inner cell row=2,col=1</para>
</entry><entry thead="no"><para>Inner cell row=2,col=2 </para>
</entry></row>
</table>
</para>
</entry><entry thead="no"><para>cell row=8,col=3 <itemizedlist>
<listitem>
<para>Item 1 </para>
</listitem>
<listitem>
<para>Item 2 </para>
</listitem>
</itemizedlist>
</para>
</entry></row>
</table>
</para>
    </detaileddescription>"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
.Complex table
[cols="3*", options="autowidth"]
|===

h| Column 1
h| Column 2
h| Column 3

.2+a| cell row=1+2,col=1
a| cell row=1,col=2
a| cell row=1,col=3

.2+a| cell row=2+3,col=2
a| cell row=2,col=3

a| cell row=3,col=1
.2+a| cell row=3+4,col=3

2+a| cell row=4,col=1+2

a| cell row=5,col=1
2+a| cell row=5,col=2+3

2.2+a| cell row=6+7,col=1+2
a| cell row=6,col=3

a| cell row=7,col=3

a| cell row=8,col=1
a| cell row=8,col=2 +
[cols="2*", options="autowidth"]
!===

a! Inner cell row=1,col=1
a! Inner cell row=1,col=2

a! Inner cell row=2,col=1
a! Inner cell row=2,col=2

!===
a| cell row=8,col=3

* Item 1

* Item 2

|==="""


def test_parse_formulae():
    input_xml = r"""<detaileddescription>
<para>The distance between <formula id="0">$(x_1,y_1)$</formula> and <formula id="1">$(x_2,y_2)$</formula> is <formula id="2">$\sqrt{(x_2-x_1)^2+(y_2-y_1)^2}$</formula>.</para>
<para><formula id="3">\[ |I_2|=\left| \int_{0}^T \psi(t) \left\{ u(a,t)- \int_{\gamma(t)}^a \frac{d\theta}{k(\theta,t)} \int_{a}^\theta c(\xi)u_t(\xi,t)\,d\xi \right\} dt \right| \]</formula></para>
<para><formula id="4">\begin{eqnarray*} g &amp;=&amp; \frac{Gm_2}{r^2} \\ &amp;=&amp; \frac{(6.673 \times 10^{-11}\,\mbox{m}^3\,\mbox{kg}^{-1}\, \mbox{s}^{-2})(5.9736 \times 10^{24}\,\mbox{kg})}{(6371.01\,\mbox{km})^2} \\ &amp;=&amp; 9.82066032\,\mbox{m/s}^2 \end{eqnarray*}</formula> </para>
    </detaileddescription>"""
    output = parse(input_xml)
    assert output.to_asciidoc(
    ) == r"""The distance between latexmath:[$(x_1,y_1)$] and latexmath:[$(x_2,y_2)$] is latexmath:[$\sqrt{(x_2-x_1)^2+(y_2-y_1)^2}$].

latexmath:[|I_2|=\left| \int_{0}^T \psi(t) \left\{ u(a,t)- \int_{\gamma(t)}^a \frac{d\theta}{k(\theta,t)} \int_{a}^\theta c(\xi)u_t(\xi,t)\,d\xi \right\} dt \right|]

latexmath:[\begin{eqnarray*} g &=& \frac{Gm_2}{r^2} \\ &=& \frac{(6.673 \times 10^{-11}\,\mbox{m}^3\,\mbox{kg}^{-1}\, \mbox{s}^{-2})(5.9736 \times 10^{24}\,\mbox{kg})}{(6371.01\,\mbox{km})^2} \\ &=& 9.82066032\,\mbox{m/s}^2 \end{eqnarray*}]"""


def test_parse_image():
    input_xml = """\
    <detaileddescription>
<para>Include images in the documentation.</para>
<para>A simple image:</para>
<para><image type="html" name="Check-256.png"></image>
</para>
<para>We can have inline <image type="html" name="User-Group-256.png" inline="yes"></image>
 images as well.</para>
<para>For accessibility we should always provide a caption:</para>
<para><image type="html" name="User-Profile-256.png">Image of a user</image>
</para>
<para>Size can be set:</para>
<para><image type="html" name="User-Group-256.png" width="50" height="100">Image of a user group</image>
 </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Include images in the documentation.

A simple image:

image::Check-256.png[]

We can have inline image:User-Group-256.png[] images as well.

For accessibility we should always provide a caption:

image::User-Profile-256.png["Image of a user"]

Size can be set:

image::User-Group-256.png["Image of a user group",50,100]"""


def test_parse_markdown():
    input_xml = """\
    <detaileddescription>
<para>Doxygen supports <ref refid="classasciidoxy_1_1descriptions_1_1_mark_down" kindref="compound">MarkDown</ref>.</para>
<para>A simple paragraph.</para>
<para>And another paragraph.</para>
<sect1 id="classasciidoxy_1_1descriptions_1_1_mark_down_1autotoc_md0">
<title>Header</title>
<para><blockquote><para>Perfection is achieved, not when there is nothing more to add, but when there is nothing left to take away. </para>
</blockquote></para>
<para><itemizedlist>
<listitem><para>List can be made with different bullets<itemizedlist>
<listitem><para>And can be nested</para>
</listitem><listitem><para>Multiple levels<itemizedlist>
<listitem><para>Even this deep</para>
</listitem><listitem><para>Do we really need that?</para>
</listitem></itemizedlist>
</para>
</listitem><listitem><para>I guess we do</para>
</listitem></itemizedlist>
</para>
</listitem><listitem><para>We should support this.</para>
</listitem></itemizedlist>
</para>
<sect2 id="classasciidoxy_1_1descriptions_1_1_mark_down_1autotoc_md1">
<title>Subheader</title>
<para><orderedlist>
<listitem><para>First item</para>
</listitem><listitem><para>Second item</para>
</listitem><listitem><para>Third item</para>
</listitem></orderedlist>
</para>
<para><hruler/>
</para>
<para>Some example code: <verbatim>int answer = 42;
</verbatim></para>
<para><strike>This is not right</strike></para>
<para><table rows="3" cols="3"><row>
<entry thead="yes" align='right'><para>Right  </para>
</entry><entry thead="yes" align='center'><para>Center  </para>
</entry><entry thead="yes" align='left'><para>Left   </para>
</entry></row>
<row>
<entry thead="no" align='right'><para>10  </para>
</entry><entry thead="no" align='center'><para>10  </para>
</entry><entry thead="no" align='left'><para>10   </para>
</entry></row>
<row>
<entry thead="no" align='right'><para>1000  </para>
</entry><entry thead="no" align='center'><para>1000  </para>
</entry><entry thead="no" align='left'><para>1000   </para>
</entry></row>
</table>
</para>
</sect2>
</sect1>
    </detaileddescription>"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Doxygen supports <<lang-classasciidoxy_1_1descriptions_1_1_mark_down,MarkDown>>.

A simple paragraph.

And another paragraph.

[discrete]
= Header

[quote]
____
Perfection is achieved, not when there is nothing more to add, but when there is nothing left to take away.
____

* List can be made with different bullets

** And can be nested

** Multiple levels

*** Even this deep

*** Do we really need that?

** I guess we do

* We should support this.

[discrete]
== Subheader

. First item

. Second item

. Third item

'''

Some example code:

----
int answer = 42;
----

[.line-through]#This is not right#

[cols="3*", options="autowidth"]
|===

>h| Right
^h| Center
h| Left

>a| 10
^a| 10
a| 10

>a| 1000
^a| 1000
a| 1000

|==="""


def test_parse_hybrid_list():
    input_xml = """\
    <detaileddescription>
<para>Combining ordered and unordered lists.</para>
<para><orderedlist>
<listitem><para>Linux<itemizedlist>
<listitem><para>ArchLinux</para>
</listitem><listitem><para>Ubuntu</para>
</listitem><listitem><para>Fedora</para>
</listitem></itemizedlist>
</para>
</listitem><listitem><para>BSD<itemizedlist>
<listitem><para>FreeBSD</para>
</listitem><listitem><para>NetBSD </para>
</listitem></itemizedlist>
</para>
</listitem></orderedlist>
</para>
    </detaileddescription>"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Combining ordered and unordered lists.

. Linux

* ArchLinux

* Ubuntu

* Fedora

. BSD

* FreeBSD

* NetBSD"""


def test_parse_failure():
    input_xml = """\
<detaileddescription>
<para><parameterlist kind="param"><parameteritem>
<parameternamelist>
<parametername>name</parametername>
</parameternamelist>
<parameterdescription>
<para>Name of the specification entry in TOML. </para>
</parameterdescription>
</parameteritem>
<parameteritem>
<parameternamelist>
<parametername>raw_spec</parametername>
</parameternamelist>
<parameterdescription>
<para>Specification entry from TOML. </para>
</parameterdescription>
</parameteritem>
<parameteritem>
<parameternamelist>
<parametername>init_args</parametername>
</parameternamelist>
<parameterdescription>
<para>Internal.</para>
</parameterdescription>
</parameteritem>
</parameterlist>
<simplesect kind="return"><para>A package specification based on the TOML contents.</para>
</simplesect>
<parameterlist kind="exception"><parameteritem>
<parameternamelist>
<parametername><ref refid="classasciidoxy_1_1packaging_1_1collect_1_1SpecificationError" kindref="compound">SpecificationError</ref></parametername>
</parameternamelist>
<parameterdescription>
<para>The specification in TOML is invalid. </para>
</parameterdescription>
</parameteritem>
</parameterlist>
</para>
        </detaileddescription>"""
    output = parse(input_xml)

    param_section = output.pop_section(ParameterList, "param")
    assert param_section is not None

    return_section = output.pop_section(Admonition, "return")
    assert return_section is not None

    exception_section = output.pop_section(ParameterList, "exception")
    assert exception_section is not None
    assert len(exception_section.contents) == 1
    assert len(list(exception_section.contents[0].names())) == 1
    name = exception_section.contents[0].first_name()
    assert not name.name
    assert not name.direction
    assert len(name.contents) == 1
    assert isinstance(name.contents[0], Ref)
    assert (
        name.contents[0].refid == "classasciidoxy_1_1packaging_1_1collect_1_1SpecificationError")

    assert not output.to_asciidoc()


def test_parse_code_blocks_no_newlines():
    input_xml = """\
    <detaileddescription>
<para>For Doxygen no new line is needed between a paragraph and a code block.</para>
<para>Python example: <programlisting filename=".py"><codeline><highlight class="keyword">class<sp/></highlight><highlight class="normal">Python:</highlight></codeline>
<codeline><highlight class="normal"><sp/><sp/><sp/><sp/></highlight><highlight class="keywordflow">pass</highlight></codeline>
</programlisting></para>
<para>C++ example: <programlisting filename=".cpp"><codeline><highlight class="keyword">class<sp/></highlight><highlight class="normal">Cpp<sp/>{};</highlight></codeline>
</programlisting> That&apos;s it! </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
For Doxygen no new line is needed between a paragraph and a code block.

Python example:

[source,python]
----
class Python:
    pass
----

C++ example:

[source,cpp]
----
class Cpp {};
----

That's it!"""


def test_parse_dashes():
    input_xml = """\
    <detaileddescription>
<para><ref refid="classasciidoxy_1_1descriptions_1_1_dashes" kindref="compound">Dashes</ref> are sometimes handled specially.</para>
<para>This is a long dash: <mdash/></para>
<para>Some shorter dashes: ...<ndash/>road1<ndash/>road2<ndash/>... </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
<<lang-classasciidoxy_1_1descriptions_1_1_dashes,Dashes>> are sometimes handled specially.

This is a long dash: &mdash;

Some shorter dashes: ...&ndash;road1&ndash;road2&ndash;..."""


def test_parse_special_characters():
    input_xml = """\
    <detaileddescription>
<para>Some special characters have specific XML representations.</para>
<para>An angle between -90<deg/> and +90<deg/>.</para>
<para>This is<nonbreakablespace/>a non breaking<nonbreakablespace/>space.</para>
<para>There are a lot of special characters, <plusmn/>250: <alpha/><beta/><frac14/> </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Some special characters have specific XML representations.

An angle between -90&deg; and +90&deg;.

This is&nbsp;a non breaking&nbsp;space.

There are a lot of special characters, &plusmn;250: &alpha;&beta;&frac14;"""


def test_parse_special_characters__all_named():
    input_characters = "".join(f"<{name}/>"
                               for name, adoc_repr in SpecialCharacter.SPECIAL_CHARACTERS.items()
                               if not adoc_repr)
    output_characters = "".join(f"&{name};"
                                for name, adoc_repr in SpecialCharacter.SPECIAL_CHARACTERS.items()
                                if not adoc_repr)
    input_xml = f"""\
    <detaileddescription>
    <para>{input_characters}</para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == output_characters


def test_parse_preformatted():
    input_xml = """\
    <detaileddescription>
<para>Developers can get creative with Ascii art in comments.</para>
<para><preformatted>
Arcs:    O----------------&gt;O---------&gt;O-----------------------&gt;O
Stretch: |            ^======================^
Route:   |       ^-------------------------------------^
         |     Origin                             Destination
         |&lt;----------&gt;|               |&lt;----&gt;|
Offsets:  front_offset               back_offset
</preformatted> </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Developers can get creative with Ascii art in comments.

----
Arcs:    O---------------->O--------->O----------------------->O
Stretch: |            ^======================^
Route:   |       ^-------------------------------------^
         |     Origin                             Destination
         |<---------->|               |<---->|
Offsets:  front_offset               back_offset
----"""


def test_parse_html_headings():
    input_xml = """\
    <detaileddescription>
<para>HTML headings are supported as well.</para>
<para><heading level="1">The top level heading.</heading>
</para>
<para>An introduction to the topic.</para>
<para><heading level="2">First subheading.</heading>
</para>
<para>More text.</para>
<para><heading level="2">Another subheading.</heading>
</para>
<para>Even more text. </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
HTML headings are supported as well.

[discrete]
= The top level heading.

An introduction to the topic.

[discrete]
== First subheading.

More text.

[discrete]
== Another subheading.

Even more text."""


def test_parse_anchor():
    input_xml = """\
    <detaileddescription>
<para>Manual anchors can be inserted in the code.</para>
<para><anchor id="classasciidoxy_1_1descriptions_1_1_anchor_1MANUAL_ANCHOR"/> You can refer back to the <ref refid="classasciidoxy_1_1descriptions_1_1_anchor_1MANUAL_ANCHOR" kindref="member">anchor</ref>. </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Manual anchors can be inserted in the code.

[#lang-classasciidoxy_1_1descriptions_1_1_anchor_1MANUAL_ANCHOR]
You can refer back to the <<lang-classasciidoxy_1_1descriptions_1_1_anchor_1MANUAL_ANCHOR,anchor>>."""


def test_parse_parblock():
    input_xml = """\
        <detaileddescription>
<para>Parblocks are used to add multiple paragraphs to commands that only accept a single parameter.</para>
<para><parameterlist kind="param"><parameteritem>
<parameternamelist>
<parametername>parameter</parametername>
</parameternamelist>
<parameterdescription>
<para><parblock><para>First paragraph about the parameter.</para>
<para>Second paragraph about the parameter. </para>
</parblock></para>
</parameterdescription>
</parameteritem>
</parameterlist>
</para>
        </detaileddescription>
"""
    output = parse(input_xml)

    param_section = output.pop_section(ParameterList, "param")
    assert param_section is not None
    assert param_section.name == "param"
    assert len(param_section.contents) == 1
    assert len(list(param_section.contents[0].names())) == 1
    name = param_section.contents[0].first_name()
    assert name.name == "parameter"
    assert not name.direction
    description = param_section.contents[0].description()
    assert description is not None
    assert description.to_asciidoc() == """\
First paragraph about the parameter.
+
Second paragraph about the parameter."""

    assert output.to_asciidoc() == """\
Parblocks are used to add multiple paragraphs to commands that only accept a single parameter."""


def test_parse_output_specific_blocks():
    input_xml = """\
    <detaileddescription>
<para>Some blocks are only to be included in specific output types.</para>
<para><docbookonly>
Don&apos;t include docbook stuff.
</docbookonly></para>
<para><manonly>
Don&apos;t include man stuff.
</manonly></para>
<para><htmlonly>
Include HTML only text.
</htmlonly></para>
<para><latexonly>
Do not include Latex here.
</latexonly></para>
<para><rtfonly>
RTF is not welcome either.
</rtfonly></para>
<para>
XML text should be included.
 </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Some blocks are only to be included in specific output types.

Include HTML only text.

XML text should be included."""


def test_parse_html_styles():
    input_xml = """\
    <detaileddescription>
<para>Some extra visual styles are possible with HTML.</para>
<para>CO<subscript>2</subscript> and X<superscript>2</superscript>.</para>
<para><ins>Inserted text</ins><linebreak/>
<del>Deleted test</del></para>
<para><underline>Underlined text</underline></para>
<para><s>Put a line through this</s></para>
<para><small>Small text</small></para>
<para><center> Some centered paragraphs.</center></para>
<para><center>Nice in the center here. </center> </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
Some extra visual styles are possible with HTML.

CO~2~ and X^2^.

+++<ins>+++Inserted text+++</ins>+++ +
+++<del>+++Deleted test+++</del>+++

[.underline]#Underlined text#

[.line-through]#Put a line through this#

[.small]#Small text#

[.text-center]
Some centered paragraphs.

[.text-center]
Nice in the center here."""


def test_parse_emoji():
    input_xml = """\
    <detaileddescription>
<para><ref refid="classasciidoxy_1_1descriptions_1_1_emoji" kindref="compound">Emoji</ref> can be used in Doxygen.</para>
<para><emoji name="smile" unicode="&amp;#x1f604;"/> I am happy</para>
<para><emoji name="cry" unicode="&amp;#x1f622;"/> I am sad</para>
<para><emoji name="star" unicode="&amp;#x2b50;"/> </para>
    </detaileddescription>
"""
    output = parse(input_xml)
    assert output.to_asciidoc() == """\
<<lang-classasciidoxy_1_1descriptions_1_1_emoji,Emoji>> can be used in Doxygen.

&#x1f604; I am happy

&#x1f622; I am sad

&#x2b50;"""


def test_select_descriptions__use_brief_and_detailed_as_in_xml():
    brief_xml = """\
    <briefdescription>
<para>Description with all kinds of Doxygen styles.</para>
    </briefdescription>
"""
    detailed_xml = """\
        <detaileddescription>
<para>Several <emphasis>words</emphasis> in this <emphasis>sentence</emphasis> are <emphasis>italic</emphasis>.</para>
<para>Several <bold>words</bold> in this <bold>sentence</bold> are <bold>bold</bold>.</para>
<para>Also a <computeroutput>some</computeroutput> words in <computeroutput>monotype</computeroutput>. </para>
        </detaileddescription>
"""
    brief, detailed = select_descriptions(parse(brief_xml), parse(detailed_xml))
    assert brief == """\
Description with all kinds of Doxygen styles."""
    assert detailed == """\
Several __words__ in this __sentence__ are __italic__.

Several **words** in this **sentence** are **bold**.

Also a ``some`` words in ``monotype``."""


def test_select_descriptions__take_first_para_from_detailed():
    brief_xml = """\
    <briefdescription>
    </briefdescription>
"""
    detailed_xml = """\
        <detaileddescription>
<para>Description with all kinds of Doxygen styles.</para>
<para>Several <emphasis>words</emphasis> in this <emphasis>sentence</emphasis> are <emphasis>italic</emphasis>.</para>
<para>Several <bold>words</bold> in this <bold>sentence</bold> are <bold>bold</bold>.</para>
<para>Also a <computeroutput>some</computeroutput> words in <computeroutput>monotype</computeroutput>. </para>
        </detaileddescription>
"""
    brief, detailed = select_descriptions(parse(brief_xml), parse(detailed_xml))
    assert brief == """\
Description with all kinds of Doxygen styles."""
    assert detailed == """\
Several __words__ in this __sentence__ are __italic__.

Several **words** in this **sentence** are **bold**.

Also a ``some`` words in ``monotype``."""


def test_select_descriptions__take_only_para_from_detailed():
    brief_xml = """\
    <briefdescription>
    </briefdescription>
"""
    detailed_xml = """\
        <detaileddescription>
<para>Description with all kinds of Doxygen styles.</para>
        </detaileddescription>
"""
    brief, detailed = select_descriptions(parse(brief_xml), parse(detailed_xml))
    assert brief == """\
Description with all kinds of Doxygen styles."""
    assert detailed == ""


def test_select_descriptions__no_descriptions_at_all():
    brief_xml = """\
    <briefdescription>
    </briefdescription>
"""
    detailed_xml = """\
        <detaileddescription>
        </detaileddescription>
"""
    brief, detailed = select_descriptions(parse(brief_xml), parse(detailed_xml))
    assert brief == ""
    assert detailed == ""
