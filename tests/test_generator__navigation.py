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
"""Tests for generating navigation for multi page output."""

import pytest

from pathlib import Path

from asciidoxy.generator.navigation import DocumentTreeNode, navigation_bar


@pytest.fixture
def document_tree_two_subpages():
    root = DocumentTreeNode(Path("/project/index.adoc"))
    sub_page1 = DocumentTreeNode(root.in_file.parent / "sub_page1.adoc", root)
    root.children.append(sub_page1)
    sub_page2 = DocumentTreeNode(root.in_file.parent / "sub_page2.adoc", root)
    root.children.append(sub_page2)
    return root


@pytest.fixture
def document_tree_two_levels_deep(document_tree_two_subpages):
    sub_page1 = document_tree_two_subpages.children[0]
    sub_page1.children.append(
        DocumentTreeNode(sub_page1.in_file.parent / "sub_page1_1.adoc", sub_page1))
    sub_page1.children.append(
        DocumentTreeNode(sub_page1.in_file.parent / "sub_page1_2.adoc", sub_page1))
    return document_tree_two_subpages


def test_document_tree_node():
    # Test tree:
    #
    #       root
    #        /|\
    #       / | \
    #      /  |  \
    #     /   |   \
    #    a    b    c
    #    /\        /\
    #   /  \      /  \
    # a_a  a_b  c_a  c_b
    #      / \
    #     /   \
    #    /     \
    #  a_b_a  a_b_b
    root = DocumentTreeNode('root')
    a = DocumentTreeNode('a', root)
    root.children.append(a)
    b = DocumentTreeNode('b', root)
    root.children.append(b)
    c = DocumentTreeNode('c', root)
    root.children.append(c)
    a_a = DocumentTreeNode('a_a', a)
    a.children.append(a_a)
    a_b = DocumentTreeNode('a_b', a)
    a.children.append(a_b)
    a_b_a = DocumentTreeNode('a_b_a', a_b)
    a_b.children.append(a_b_a)
    a_b_b = DocumentTreeNode('a_b_b', a_b)
    a_b.children.append(a_b_b)
    c_a = DocumentTreeNode('c_a', c)
    c.children.append(c_a)
    c_b = DocumentTreeNode('c_b', c)
    c.children.append(c_b)

    def verify_node(node: DocumentTreeNode, expected_parent: DocumentTreeNode,
                    expected_prev: DocumentTreeNode, expected_next: DocumentTreeNode):
        assert node.root() is root
        assert node.parent is expected_parent
        assert node.preorder_traversal_prev() is expected_prev
        assert node.preorder_traversal_next() is expected_next

    verify_node(root, expected_parent=None, expected_prev=None, expected_next=a)
    verify_node(a, expected_parent=root, expected_prev=root, expected_next=a_a)
    verify_node(a_a, expected_parent=a, expected_prev=a, expected_next=a_b)
    verify_node(a_b, expected_parent=a, expected_prev=a_a, expected_next=a_b_a)
    verify_node(a_b_a, expected_parent=a_b, expected_prev=a_b, expected_next=a_b_b)
    verify_node(a_b_b, expected_parent=a_b, expected_prev=a_b_a, expected_next=b)
    verify_node(b, expected_parent=root, expected_prev=a_b_b, expected_next=c)
    verify_node(c, expected_parent=root, expected_prev=b, expected_next=c_a)
    verify_node(c, expected_parent=root, expected_prev=b, expected_next=c_a)
    verify_node(c_a, expected_parent=c, expected_prev=c, expected_next=c_b)
    verify_node(c_b, expected_parent=c, expected_prev=c_a, expected_next=None)


def test_document_tree_node_all_documents_from_root_node(document_tree_two_levels_deep):

    assert ({str(d.in_file)
             for d in document_tree_two_levels_deep.all_documents_in_tree()} == {
                 "/project/index.adoc", "/project/sub_page1.adoc", "/project/sub_page2.adoc",
                 "/project/sub_page1_1.adoc", "/project/sub_page1_2.adoc"
             })


def test_document_tree_node_all_documents_from_middle_node(document_tree_two_levels_deep):
    middle_doc = document_tree_two_levels_deep.children[1]

    assert ({str(d.in_file)
             for d in middle_doc.all_documents_in_tree()} == {
                 "/project/index.adoc", "/project/sub_page1.adoc", "/project/sub_page2.adoc",
                 "/project/sub_page1_1.adoc", "/project/sub_page1_2.adoc"
             })


def test_document_tree_node_all_documents_from_leaf_node(document_tree_two_levels_deep):
    leaf_doc = document_tree_two_levels_deep.children[0].children[0]

    assert ({str(d.in_file)
             for d in leaf_doc.all_documents_in_tree()} == {
                 "/project/index.adoc", "/project/sub_page1.adoc", "/project/sub_page2.adoc",
                 "/project/sub_page1_1.adoc", "/project/sub_page1_2.adoc"
             })


def test_navigation_bar_first_document(document_tree_two_subpages):
    next_doc = document_tree_two_subpages.children[0]
    assert navigation_bar(document_tree_two_subpages) == (
        f"""[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|

|

|<<{next_doc.in_file.relative_to(document_tree_two_subpages.in_file.parent)}#,Next>>
|===""")


def test_navigation_bar_middle_document(document_tree_two_subpages):
    doc = document_tree_two_subpages.children[0]
    next_doc = document_tree_two_subpages.children[1]
    assert navigation_bar(doc) == (f"""[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|<<{document_tree_two_subpages.in_file.relative_to(doc.in_file.parent)}#,Prev>>

|<<{document_tree_two_subpages.in_file.relative_to(doc.in_file.parent)}#,Up>> +
<<{document_tree_two_subpages.in_file.relative_to(doc.in_file.parent)}#,Home>>

|<<{next_doc.in_file.relative_to(document_tree_two_subpages.in_file.parent)}#,Next>>
|===""")


def test_navigation_bar_last_document(document_tree_two_subpages):
    doc = document_tree_two_subpages.children[1]
    prev_doc = document_tree_two_subpages.children[0]
    assert navigation_bar(doc) == (f"""[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|<<{prev_doc.in_file.relative_to(doc.in_file.parent)}#,Prev>>

|<<{document_tree_two_subpages.in_file.relative_to(doc.in_file.parent)}#,Up>> +
<<{document_tree_two_subpages.in_file.relative_to(doc.in_file.parent)}#,Home>>

|
|===""")


def test_navigation_bar_all_links_different(document_tree_two_levels_deep):
    doc = document_tree_two_levels_deep.children[0].children[1]
    prev_doc = document_tree_two_levels_deep.children[0].children[0]
    next_doc = document_tree_two_levels_deep.children[1]
    up_doc = document_tree_two_levels_deep.children[0]

    assert navigation_bar(doc) == (f"""[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|<<{prev_doc.in_file.relative_to(doc.in_file.parent)}#,Prev>>

|<<{up_doc.in_file.relative_to(doc.in_file.parent)}#,Up>> +
<<{document_tree_two_levels_deep.in_file.relative_to(doc.in_file.parent)}#,Home>>

|<<{next_doc.in_file.relative_to(doc.in_file.parent)}#,Next>>
|===""")


def test_navigation_bar_single_document():
    doc = DocumentTreeNode("/project/index.adoc")
    assert not navigation_bar(doc)
