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
"""Tests for generating navigation for multi page output."""

from asciidoxy.generator.navigation import multipage_toc, navigation_bar


def test_navigation_bar_first_document(document_tree):
    assert navigation_bar(document_tree["root"]) == """\
ifdef::backend-html5[]
++++
<div id="navigation">
++++
endif::[]
[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|

|

|<<a.adoc#,Next>>
|===
ifdef::backend-html5[]
++++
</div>
++++
endif::[]"""


def test_navigation_bar_middle_document(document_tree):
    assert navigation_bar(document_tree["a/a_b"]) == """\
ifdef::backend-html5[]
++++
<div id="navigation">
++++
endif::[]
[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|<<a_a.adoc#,Prev>>

|<<../a.adoc#,Up>> +
<<../root.adoc#,Home>>

|<<b/a_b_a.adoc#,Next>>
|===
ifdef::backend-html5[]
++++
</div>
++++
endif::[]"""


def test_navigation_bar_last_document(document_tree):
    assert navigation_bar(document_tree["c/c_b"]) == """\
ifdef::backend-html5[]
++++
<div id="navigation">
++++
endif::[]
[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|<<c_a.adoc#,Prev>>

|<<../c.adoc#,Up>> +
<<../root.adoc#,Home>>

|
|===
ifdef::backend-html5[]
++++
</div>
++++
endif::[]"""


def test_navigation_bar_single_document(document):
    assert not navigation_bar(document)


def test_multipage_toc__root_level(document_tree):
    assert multipage_toc(document_tree["root"]) == """\
<div class="toc2" id="toc" style="left: 0; right: unset; border-right-width: 1px; border-left-width: 0px">
  <div id="toctitle">
    <a href="root.html">root</a>
  </div>
  <ul class="sectlevel1">
    <li>
      <a href="a.html">a</a>
    </li>
    <li>
      <a href="b.html">b</a>
    </li>
    <li>
      <a href="c.html">c</a>
    </li>
  </ul>
</div>
"""


def test_multipage_toc__level1__child0(document_tree):
    assert multipage_toc(document_tree["a"]) == """\
<div class="toc2" id="toc" style="left: 0; right: unset; border-right-width: 1px; border-left-width: 0px">
  <div id="toctitle">
    <a href="root.html">root</a>
  </div>
  <ul class="sectlevel1">
    <li>
      <a href="a.html">a</a>
      <ul class="sectlevel2">
        <li>
          <a href="a/a_a.html">a_a</a>
        </li>
        <li>
          <a href="a/a_b.html">a_b</a>
        </li>
      </ul>
    </li>
    <li>
      <a href="b.html">b</a>
    </li>
    <li>
      <a href="c.html">c</a>
    </li>
  </ul>
</div>
"""


def test_multipage_toc__level1__child1(document_tree):
    assert multipage_toc(document_tree["b"]) == """\
<div class="toc2" id="toc" style="left: 0; right: unset; border-right-width: 1px; border-left-width: 0px">
  <div id="toctitle">
    <a href="root.html">root</a>
  </div>
  <ul class="sectlevel1">
    <li>
      <a href="a.html">a</a>
    </li>
    <li>
      <a href="b.html">b</a>
    </li>
    <li>
      <a href="c.html">c</a>
    </li>
  </ul>
</div>
"""


def test_multipage_toc__level1__child2(document_tree):
    assert multipage_toc(document_tree["c"]) == """\
<div class="toc2" id="toc" style="left: 0; right: unset; border-right-width: 1px; border-left-width: 0px">
  <div id="toctitle">
    <a href="root.html">root</a>
  </div>
  <ul class="sectlevel1">
    <li>
      <a href="a.html">a</a>
    </li>
    <li>
      <a href="b.html">b</a>
    </li>
    <li>
      <a href="c.html">c</a>
      <ul class="sectlevel2">
        <li>
          <a href="c/c_a.html">c_a</a>
        </li>
        <li>
          <a href="c/c_b.html">c_b</a>
        </li>
      </ul>
    </li>
  </ul>
</div>
"""


def test_multipage_toc__level2__child0(document_tree):
    assert multipage_toc(document_tree["a/a_a"]) == """\
<div class="toc2" id="toc" style="left: 0; right: unset; border-right-width: 1px; border-left-width: 0px">
  <div id="toctitle">
    <a href="../root.html">root</a>
  </div>
  <ul class="sectlevel1">
    <li>
      <a href="../a.html">a</a>
      <ul class="sectlevel2">
        <li>
          <a href="a_a.html">a_a</a>
        </li>
        <li>
          <a href="a_b.html">a_b</a>
        </li>
      </ul>
    </li>
    <li>
      <a href="../b.html">b</a>
    </li>
    <li>
      <a href="../c.html">c</a>
    </li>
  </ul>
</div>
"""


def test_multipage_toc__level2__child1(document_tree):
    assert multipage_toc(document_tree["a/a_b"]) == """\
<div class="toc2" id="toc" style="left: 0; right: unset; border-right-width: 1px; border-left-width: 0px">
  <div id="toctitle">
    <a href="../root.html">root</a>
  </div>
  <ul class="sectlevel1">
    <li>
      <a href="../a.html">a</a>
      <ul class="sectlevel2">
        <li>
          <a href="a_a.html">a_a</a>
        </li>
        <li>
          <a href="a_b.html">a_b</a>
          <ul class="sectlevel3">
            <li>
              <a href="b/a_b_a.html">a_b_a</a>
            </li>
            <li>
              <a href="b/a_b_b.html">a_b_b</a>
            </li>
          </ul>
        </li>
      </ul>
    </li>
    <li>
      <a href="../b.html">b</a>
    </li>
    <li>
      <a href="../c.html">c</a>
    </li>
  </ul>
</div>
"""


def test_multipage_toc__level3(document_tree):
    assert multipage_toc(document_tree["a/b/a_b_a"]) == """\
<div class="toc2" id="toc" style="left: 0; right: unset; border-right-width: 1px; border-left-width: 0px">
  <div id="toctitle">
    <a href="../../root.html">root</a>
  </div>
  <ul class="sectlevel1">
    <li>
      <a href="../../a.html">a</a>
      <ul class="sectlevel2">
        <li>
          <a href="../a_a.html">a_a</a>
        </li>
        <li>
          <a href="../a_b.html">a_b</a>
          <ul class="sectlevel3">
            <li>
              <a href="a_b_a.html">a_b_a</a>
            </li>
            <li>
              <a href="a_b_b.html">a_b_b</a>
            </li>
          </ul>
        </li>
      </ul>
    </li>
    <li>
      <a href="../../b.html">b</a>
    </li>
    <li>
      <a href="../../c.html">c</a>
    </li>
  </ul>
</div>
"""


def test_multipage_toc__left_side(document_tree):
    assert multipage_toc(document_tree["root"], side="left") == """\
<div class="toc2" id="toc" style="left: 0; right: unset; border-right-width: 1px; border-left-width: 0px">
  <div id="toctitle">
    <a href="root.html">root</a>
  </div>
  <ul class="sectlevel1">
    <li>
      <a href="a.html">a</a>
    </li>
    <li>
      <a href="b.html">b</a>
    </li>
    <li>
      <a href="c.html">c</a>
    </li>
  </ul>
</div>
"""


def test_multipage_toc__right_side(document_tree):
    assert multipage_toc(document_tree["root"], side="right") == """\
<div class="toc2" id="toc" style="left: unset; right: 0; border-right-width: 0px; border-left-width: 1px">
  <div id="toctitle">
    <a href="root.html">root</a>
  </div>
  <ul class="sectlevel1">
    <li>
      <a href="a.html">a</a>
    </li>
    <li>
      <a href="b.html">b</a>
    </li>
    <li>
      <a href="c.html">c</a>
    </li>
  </ul>
</div>
"""
