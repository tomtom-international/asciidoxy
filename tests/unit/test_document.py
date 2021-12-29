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
"""Test for the document abstractions and helpers."""

from pathlib import Path

import pytest
import toml

from asciidoxy.document import Document, Package


def test_package__from_toml(tmp_path):
    contents = """\
[package]
name = "package"

[reference]
type = "doxygen"
dir = "xml"

[asciidoc]
src_dir = "adoc"
image_dir = "images"
root_doc = "index.adoc"
"""

    pkg = Package("my-package")
    pkg.load_from_toml(tmp_path, toml.loads(contents))

    assert pkg.name == "package"
    assert pkg.scoped is True
    assert pkg.reference_type == "doxygen"
    assert pkg.reference_dir == tmp_path / "xml"
    assert pkg.adoc_src_dir == tmp_path / "adoc"
    assert pkg.adoc_image_dir == tmp_path / "images"
    assert pkg.adoc_root_doc == tmp_path / "adoc" / "index.adoc"


def test_package__from_toml__no_name(tmp_path):
    contents = """\
[package]

[reference]
type = "doxygen"
dir = "xml"

[asciidoc]
src_dir = "adoc"
image_dir = "images"
root_doc = "index.adoc"
"""

    pkg = Package("my-package")
    pkg.load_from_toml(tmp_path, toml.loads(contents))

    assert pkg.name == "my-package"
    assert pkg.scoped is True
    assert pkg.reference_type == "doxygen"
    assert pkg.reference_dir == tmp_path / "xml"
    assert pkg.adoc_src_dir == tmp_path / "adoc"
    assert pkg.adoc_image_dir == tmp_path / "images"
    assert pkg.adoc_root_doc == tmp_path / "adoc" / "index.adoc"


def test_package__from_toml__no_reference(tmp_path):
    contents = """\
[package]
name = "package"

[asciidoc]
src_dir = "adoc"
image_dir = "images"
root_doc = "index.adoc"
"""

    pkg = Package("my-package")
    pkg.load_from_toml(tmp_path, toml.loads(contents))

    assert pkg.name == "package"
    assert pkg.scoped is True
    assert pkg.reference_type is None
    assert pkg.reference_dir is None
    assert pkg.adoc_src_dir == tmp_path / "adoc"
    assert pkg.adoc_image_dir == tmp_path / "images"
    assert pkg.adoc_root_doc == tmp_path / "adoc" / "index.adoc"


def test_package__from_toml__no_asciidoc(tmp_path):
    contents = """\
[package]
name = "package"

[reference]
type = "doxygen"
dir = "xml"
"""

    pkg = Package("my-package")
    pkg.load_from_toml(tmp_path, toml.loads(contents))

    assert pkg.name == "package"
    assert pkg.scoped is True
    assert pkg.reference_type == "doxygen"
    assert pkg.reference_dir == tmp_path / "xml"
    assert pkg.adoc_src_dir is None
    assert pkg.adoc_image_dir is None
    assert pkg.adoc_root_doc is None


def test_package__from_toml__root_doc_no_src_dir(tmp_path):
    contents = """\
[package]
name = "package"

[reference]
type = "doxygen"
dir = "xml"

[asciidoc]
root_doc = "index.adoc"
"""

    pkg = Package("my-package")
    pkg.load_from_toml(tmp_path, toml.loads(contents))

    assert pkg.name == "package"
    assert pkg.scoped is True
    assert pkg.reference_type == "doxygen"
    assert pkg.reference_dir == tmp_path / "xml"
    assert pkg.adoc_src_dir is None
    assert pkg.adoc_image_dir is None
    assert pkg.adoc_root_doc is None


def test_document__file_paths(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)

    assert doc.original_file == pkg_dir / "dir/index.adoc"
    assert doc.work_file == work_dir / "dir/index.adoc"
    assert doc.docinfo_footer_file == work_dir / "dir/index-docinfo-footer.html"


def test_document__relative_path_to__same_dir(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir

    doc1 = Document(Path("dir/index.adoc"), pkg, work_dir)
    doc2 = Document(Path("dir/other.adoc"), pkg, work_dir)

    assert doc1.relative_path_to(doc2) == Path("other.adoc")
    assert doc2.relative_path_to(doc1) == Path("index.adoc")


def test_document__relative_path_to__subdir(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir

    doc1 = Document(Path("dir/index.adoc"), pkg, work_dir)
    doc2 = Document(Path("dir/sub/other.adoc"), pkg, work_dir)

    assert doc1.relative_path_to(doc2) == Path("sub/other.adoc")
    assert doc2.relative_path_to(doc1) == Path("../index.adoc")


def test_document__relative_path_to__other_dir(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir

    doc1 = Document(Path("dir1/index.adoc"), pkg, work_dir)
    doc2 = Document(Path("dir2/sub/other.adoc"), pkg, work_dir)

    assert doc1.relative_path_to(doc2) == Path("../dir2/sub/other.adoc")
    assert doc2.relative_path_to(doc1) == Path("../../dir1/index.adoc")


def test_document__resolve_relative_path(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)

    assert doc.resolve_relative_path("other.adoc") == Path("dir/other.adoc")
    assert doc.resolve_relative_path("../other.adoc") == Path("other.adoc")
    assert doc.resolve_relative_path("../sub/other.adoc") == Path("sub/other.adoc")
    assert doc.resolve_relative_path("sub/other.adoc") == Path("dir/sub/other.adoc")


def test_document__title(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)
    doc.original_file.parent.mkdir(parents=True)
    doc.original_file.write_text("= My title\n\nOther text.")

    assert doc.title == "My title"


def test_document__title__only_first_title(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)
    doc.original_file.parent.mkdir(parents=True)
    doc.original_file.write_text("= My title\n\nOther text.\n\n= Other title\n\nMore text.")

    assert doc.title == "My title"


def test_document__title__no_title(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)
    doc.original_file.parent.mkdir(parents=True)
    doc.original_file.write_text("My title\n\nOther text.\n\n== Other title\n\nMore text.")

    assert doc.title == "index"


def test_document__title__no_file(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)
    doc.original_file.parent.mkdir(parents=True)
    assert not doc.original_file.exists()

    assert doc.title == "index"


@pytest.mark.parametrize("content,title", [
    ("= *My title*", "My title"),
    ("= **My title**", "My title"),
    ("= _My_ title", "My title"),
    ("= __My__ title", "My title"),
    ("= `*__My__ title*`", "My title"),
    ("= My title[[anchor,anchor]]", "My title"),
    ("= My title [[anchor,anchor]]", "My title"),
    ("= My ^title^", "My title"),
    ("= My ~title~", "My title"),
    ("= [.big]#My# title", "My title"),
    ("= [.big]##My## title", "My title"),
])
def test_document__title__remove_formatting(tmp_path, content, title):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)
    doc.original_file.parent.mkdir(parents=True)
    doc.original_file.write_text(content)

    assert doc.title == title


def test_document__not_used(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)

    assert doc.is_used is False
    assert doc.is_included is False
    assert doc.is_embedded is False


def test_document__included(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)
    parent_doc = Document(Path("dir/index.adoc"), pkg, work_dir)
    parent_doc.include(doc)

    assert doc.is_used is True
    assert doc.is_included is True
    assert doc.is_embedded is False
    assert doc in parent_doc.children
    assert doc.included_in is parent_doc
    assert parent_doc not in doc.embedded_in


def test_document__embedded(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)
    parent_doc = Document(Path("dir/index.adoc"), pkg, work_dir)
    parent_doc.embed(doc)

    assert doc.is_used is True
    assert doc.is_included is False
    assert doc.is_embedded is True
    assert doc in parent_doc.children
    assert parent_doc in doc.embedded_in


def test_document__root_doc(tmp_path):
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"

    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir
    doc = Document(Path("dir/index.adoc"), pkg, work_dir)
    doc.is_root = True

    assert doc.is_used is True
    assert doc.is_included is False
    assert doc.is_embedded is False


def test_document__root(document_tree):
    root = document_tree["root"]
    for doc in document_tree.values():
        assert doc.root() is root


def test_document__root__not_is_root(document_tree):
    root = document_tree["root"]
    root.is_root = False
    for doc in document_tree.values():
        assert doc.root() is root


def test_document__root__orphaned(document_tree):
    a = document_tree["a"]
    a.included_in = None
    for name in ("a", "a/a_a", "a/a_b", "a/b/a_b_a", "a/b/a_b_b", "a/a/a_a_emb"):
        assert document_tree[name].root() is a


def test_document__find_embedder(document_tree):
    for name in ("root", "a", "b", "c", "a/a_a", "a/a_b", "c/c_a", "c/c_b", "a/b/a_b_a",
                 "a/b/a_b_b"):
        assert document_tree[name].find_embedder() is document_tree[name]

    assert document_tree["a/a/a_a_emb"].find_embedder() is document_tree["a/a_a"]

    for name in ("c/c_emb", "c/c_emb_emb"):
        assert document_tree[name].find_embedder() in (document_tree["c"], document_tree["c/c_a"],
                                                       document_tree["c/c_b"])


def test_document__is_embedded_in(document_tree):
    not_embedded = ("root", "a", "b", "c", "a/a_a", "a/a_b", "c/c_a", "c/c_b", "a/b/a_b_a",
                    "a/b/a_b_b")
    for name in not_embedded:
        for name_again in not_embedded:
            assert document_tree[name].is_embedded_in(document_tree[name_again]) is False

    assert document_tree["a/a/a_a_emb"].is_embedded_in(document_tree["a/a_a"]) is True
    for name in ("root", "a", "b", "c", "a/a_b", "c/c_a", "c/c_b", "a/b/a_b_a", "a/b/a_b_b"):
        assert document_tree["a/a/a_a_emb"].is_embedded_in(document_tree[name]) is False

    assert document_tree["c/c_emb"].is_embedded_in(document_tree["c"]) is True
    assert document_tree["c/c_emb"].is_embedded_in(document_tree["c/c_a"]) is True
    assert document_tree["c/c_emb"].is_embedded_in(document_tree["c/c_a"]) is True
    assert document_tree["c/c_emb_emb"].is_embedded_in(document_tree["c"]) is True
    assert document_tree["c/c_emb_emb"].is_embedded_in(document_tree["c/c_a"]) is True
    assert document_tree["c/c_emb_emb"].is_embedded_in(document_tree["c/c_b"]) is True
    assert document_tree["c/c_emb_emb"].is_embedded_in(document_tree["c/c_emb"]) is True

    for name in ("root", "a", "b", "a/a_a", "a/a_b", "a/b/a_b_a", "a/b/a_b_b"):
        assert document_tree["c/c_emb"].is_embedded_in(document_tree[name]) is False
        assert document_tree["c/c_emb_emb"].is_embedded_in(document_tree[name]) is False


def test_document__preorder_next(document_tree):
    doc = document_tree["root"]
    for expected_next in ("a", "a/a_a", "a/a_b", "a/b/a_b_a", "a/b/a_b_b", "b", "c", "c/c_a",
                          "c/c_b"):
        doc = doc.preorder_next()
        assert doc is document_tree[expected_next]
    assert doc.preorder_next() is None


def test_document__preorder_prev(document_tree):
    doc = document_tree["c/c_b"]
    for expected_prev in ("c/c_a", "c", "b", "a/b/a_b_b", "a/b/a_b_a", "a/a_b", "a/a_a", "a",
                          "root"):
        doc = doc.preorder_prev()
        assert doc == document_tree[expected_prev]
    assert doc.preorder_prev() is None


def test_document__iter_all(document_tree):
    expected_order = [
        document_tree[name] for name in ("root", "a", "a/a_a", "a/a_b", "a/b/a_b_a", "a/b/a_b_b",
                                         "b", "c", "c/c_a", "c/c_b")
    ]
    for start in expected_order:
        assert list(start.iter_all()) == expected_order
