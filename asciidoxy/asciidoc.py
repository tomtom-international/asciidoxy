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
"""Generation of AsciiDoc output."""

import functools
import json
import logging
import os

from mako.exceptions import TopLevelLookupException
from mako.lookup import TemplateLookup
from mako.template import Template
from pathlib import Path
from typing import Collection, Dict, List, MutableMapping, NamedTuple, Optional, Tuple

from . import templates
from .api_reference import AmbiguousLookupError, ApiReference
from .doxygen_xml import DoxygenXmlParser, safe_language_tag
from .model import Member, ReferableElement, json_repr

logger = logging.getLogger(__name__)

warnings_are_errors = False
multi_page = False


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


class DocumentTreeNode(object):
    """A node in the hierarchical tree of documents.

    The tree represents the structure of the documentation. The node can represent either a root
    document, an intermediate document or a leaf document.

    Attributes:
        in_file: File from which the node was read.
        parent: Parent node in the tree.
        children: Child nodes in the tree.
    """
    in_file: Path
    parent: Optional["DocumentTreeNode"]
    children: List["DocumentTreeNode"]

    def __init__(self, in_file: Path, parent: "DocumentTreeNode" = None):
        self.in_file = in_file
        self.parent = parent
        self.children = []

    def preorder_traversal_next(self):
        if len(self.children) > 0:
            return self.children[0]
        return self._next_subtree()

    def preorder_traversal_prev(self):
        if self.parent is None:
            return None
        i, this_doc = self.parent._find_child(self.in_file)
        assert this_doc is not None
        return self.parent.children[i - 1]._last_leaf() if i > 0 else self.parent

    def find_child(self, child_in_file: Path):
        _, child = self._find_child(child_in_file)
        return child

    def root(self):
        return self if self.parent is None else self.parent.root()

    def all_documents_in_tree(self):
        return self.root()._all_documents_in_subtree()

    def _next_subtree(self):
        if self.parent is None:
            return None
        i, this_doc = self.parent._find_child(self.in_file)
        assert this_doc is not None
        if len(self.parent.children) > i + 1:
            return self.parent.children[i + 1]
        return self.parent._next_subtree()

    def _last_leaf(self):
        if len(self.children) == 0:
            return self
        return self.children[-1]._last_leaf()

    def _find_child(self, in_file: Path) -> Tuple[int, Optional["DocumentTreeNode"]]:
        for i, elem in enumerate(self.children):
            if (elem.in_file == in_file):
                return (i, elem)
        return (0, None)

    def _all_documents_in_subtree(self):
        yield self
        for child in self.children:
            for d in child._all_documents_in_subtree():
                yield d


class Context(object):
    """Contextual information about the document being generated.

    This information is meant to be shared with all included documents as well.

    Attributes:
        base_dir:           Base directory from which the documentation is generated. Relative
                                paths are relative to the base directory.
        build_dir:          Directory for (temporary) build artifacts.
        fragment_dir:       Directory containing generated fragments to be included in the
                                documentation.
        namespace:          Current namespace to use when looking up references.
        language:           Default language to use when looking up references.
        preprocessing_run:  True when preprocessing. During preprocessing no files are generated.
        reference:          API reference information.
        linked:             All elements to which links are inserted in the documentation.
        inserted:           All elements that have been inserted in the documentation.
        in_to_out_file_map: Mapping from input files for AsciiDoctor to the resulting output files.
        current_document:   Node in the Document Tree that is currently being processed.
    """
    base_dir: Path
    build_dir: Path
    fragment_dir: Path

    namespace: Optional[str] = None
    language: Optional[str] = None

    preprocessing_run: bool

    reference: ApiReference

    linked: List[ReferableElement]
    inserted: MutableMapping[str, Path]
    in_to_out_file_map: Dict[Path, Path]
    current_document: DocumentTreeNode

    def __init__(self, base_dir: Path, build_dir: Path, fragment_dir: Path, reference: ApiReference,
                 current_document: DocumentTreeNode):
        self.base_dir = base_dir
        self.build_dir = build_dir
        self.fragment_dir = fragment_dir

        self.preprocessing_run = True

        self.reference = reference

        self.linked = []
        self.inserted = {}
        self.in_to_out_file_map = {}
        self.current_document = current_document

    def insert(self, element) -> str:
        if self.preprocessing_run:
            if element.id in self.inserted:
                msg = f"Duplicate insertion of {element.name}"
                if warnings_are_errors:
                    raise ConsistencyError(msg)
                else:
                    logger.warning(msg)
            self.inserted[element.id] = self.current_document.in_file

        return ""  # Prevent output in templates

    def sub_context(self) -> "Context":
        sub = Context(base_dir=self.base_dir,
                      build_dir=self.build_dir,
                      fragment_dir=self.fragment_dir,
                      reference=self.reference,
                      current_document=self.current_document)

        # Copies
        sub.namespace = self.namespace
        sub.language = self.language
        sub.preprocessing_run = self.preprocessing_run

        # References
        sub.linked = self.linked
        sub.inserted = self.inserted
        sub.in_to_out_file_map = self.in_to_out_file_map

        return sub

    def link_to_element(self,
                        element_id: str,
                        link_text: str,
                        element: Optional[ReferableElement] = None) -> str:
        def file_part():
            if not multi_page or element_id not in self.inserted:
                return ""
            containing_file = self.inserted[element_id]
            assert containing_file is not None
            if self.current_document.in_file != containing_file:
                return f"{_relative_path(self.current_document.in_file, containing_file)}#"

        if element is None:
            element = self.reference.find(target_id=element_id)
        if element is not None:
            self.linked.append(element)

        return f"xref:{file_part() or ''}{element_id}[{link_text}]"


class Api(object):
    """Methods to insert and link to API reference documentation from AsciiDoc files."""
    class TemplateKey(NamedTuple):
        lang: str
        kind: str

    _template_cache: MutableMapping[TemplateKey, Template] = {}

    _current_file: Path
    _context: Context

    def __init__(self, current_file: Path, context: Context):
        assert current_file.is_file()
        assert context.base_dir.is_dir()
        assert context.build_dir.is_dir()
        assert context.fragment_dir.is_dir()
        assert context.reference is not None

        self._current_file = current_file

        self._context = context

    def __getattr__(self, name: str):
        if name.startswith("insert_"):
            return functools.partial(self.insert, kind=name[7:])
        elif name.startswith("link_"):
            return functools.partial(self.link, kind=name[5:])
        else:
            raise AttributeError(name)

    def find_element(self,
                     name: str,
                     *,
                     kind: Optional[str] = None,
                     lang: Optional[str] = None) -> ReferableElement:
        """Find a reference to API documentation.

        Only `name` is mandatory. Multiple names may match the same name. Use `kind` and `lang` to
        disambiguate.

        Args:
            name: Name of the object to insert.
            kind: Kind of object to generate reference documentation for.
            lang: Programming language of the object.

        Returns:
            An API documentation reference.

        Raises:
             AmbiguousReferenceError: There are multiple elements matching the criteria.
             ReferenceNotFoundError: There are no elements matching the criteria.
        """
        if lang is not None:
            lang = safe_language_tag(lang)
        else:
            lang = self._context.language

        try:
            element = self._context.reference.find(name=name,
                                                   namespace=self._context.namespace,
                                                   kind=kind,
                                                   lang=lang)
        except AmbiguousLookupError as ex:
            raise AmbiguousReferenceError(name, ex.candidates)

        if element is None:
            raise ReferenceNotFoundError(name, lang=lang, kind=kind)
        return element

    def insert(self,
               name: str,
               *,
               kind: Optional[str] = None,
               lang: Optional[str] = None,
               leveloffset: str = "+1") -> str:
        """Insert API reference documentation.

        Only `name` is mandatory. Multiple names may match the same name. Use `kind` and `lang` to
        disambiguate.

        Args:
            name:        Fully qualified name of the object to insert.
            kind:        Kind of object to generate reference documentation for.
            lang:        Programming language of the object.
            leveloffset: Offset of the top header of the inserted text from the top level header
                             of the including document.

        Returns:
            AsciiDoc text to include in the document.
        """
        return self.insert_fragment(self.find_element(name, kind=kind, lang=lang), leveloffset)

    def link(self,
             name: str,
             *,
             kind: Optional[str] = None,
             lang: Optional[str] = None,
             text: Optional[str] = None,
             full_name: bool = False) -> str:
        """Insert a link to API reference documentation.

        Only `name` is mandatory. Multiple names may match the same name. Use `kind` and `lang` to
        disambiguate.

        Args:
            name:      Fully qualified name of the object to link to.
            kind:      Kind of object to link to.
            lang:      Programming language of the object.
            text:      Alternative text to use for the link. If not supplied, the object name is
                           used.
            full_name: Use the fully qualified name of the object for the link text.

        Returns:
            AsciiDoc text to include in the document.
        """
        if text is not None and full_name is True:
            raise ValueError("`text` and `full_name` cannot be used together.")

        try:
            element = self.find_element(name, kind=kind, lang=lang)
        except ReferenceNotFoundError as ref_not_found:
            if warnings_are_errors:
                raise
            else:
                logger.warning(str(ref_not_found))
                return text or name

        if element.id is None:
            unlinkable = UnlinkableError(name, lang=lang, kind=kind)
            if warnings_are_errors:
                raise unlinkable
            else:
                logger.warning(str(unlinkable))
                return text or name

        if text is not None:
            link_text = text
        elif full_name:
            link_text = name
        else:
            link_text = element.name

        return self._context.link_to_element(element.id, link_text, element)

    def cross_document_ref(self, file_name: str, anchor: str, link_text: str = None) -> str:
        """AsciiDoc cross-document reference.

        Since AsciiDoxy in multi-page mode generates intermediate AsciiDoc files and process them
        with AsciiDoctor in order to create final output document(s) the direct AsciiDoc syntax
        (i.e. `<<file_name#anchor,link_tex>>`) doesn't work. You must use this method instead.

        Args:
             file_name: Relative or absolute path to the referred AsciiDoc file. Relative paths
                            are relative to the document calling the method.
             anchor:    Anchor to the referred section in the referred AsciiDoc document.
             link_text: Text of the reference. If None, `anchor` will be used as text of the
                            reference.

        Returns:
            AsciiDoc cross-document reference.
        """
        referenced_file_name = Path(file_name)

        if not self._context.preprocessing_run:
            absolute_file_path = (referenced_file_name if referenced_file_name.is_absolute() else
                                  self._current_file.parent / referenced_file_name).resolve()
            if absolute_file_path not in (
                    d.in_file for d in self._context.current_document.all_documents_in_tree()):
                msg = (f"Invalid cross-reference from document '{self._current_file}' "
                       f"to document: '{file_name}'. The referenced document: {absolute_file_path} "
                       f"is not included anywhere across whole documentation tree.")
                if warnings_are_errors:
                    raise ConsistencyError(msg)
                else:
                    logger.warning(msg)

        if not multi_page:
            file_path = Path(file_name)
            if not file_path.is_absolute():
                file_path = (self._current_file.parent / file_path).resolve().relative_to(
                    self._context.base_dir)
            referenced_file_name = _out_file_name(file_path)
        return (f"<<{referenced_file_name}#{anchor},"
                f"{link_text if link_text is not None else anchor}>>")

    def insert_fragment(self, element, leveloffset: str = "+1") -> str:
        """Generate and insert a documentation fragment.

        Args:
            element:     Python representation of the element to insert.
            leveloffset: Offset of the top header of the inserted text from the top level header
                             of the including document.

        Returns:
            AsciiDoc text to include in the document.
        """

        assert element.id
        fragment_file = self._context.fragment_dir / f"{element.id}.adoc"

        rendered_doc = self._template(element.language,
                                      element.kind).render(element=element,
                                                           api_context=self._context,
                                                           api=self)

        if not self._context.preprocessing_run:
            with fragment_file.open("w", encoding="utf-8") as f:
                print(rendered_doc, file=f)

        return f"include::{fragment_file}[leveloffset={leveloffset}]"

    def include(self,
                file_name: str,
                leveloffset: str = "+1",
                link_text: str = "",
                link_prefix: str = "",
                multi_page_link: bool = True) -> str:
        """Include another AsciiDoc file, and process it to insert API references.

        If the output format is multi-paged, the method will cause generation of separate output
        document for the included AsciiDoc document and optional insertion of link referring to the
        document.

        Args:
            file_name:         Relative or absolute path to the file to include. Relative paths are
                                   relative to the document calling include.
            leveloffset:       Offset of the top header of the inserted text from the top level
                                   header of the including document.
            link_text:         Text of the link which will be inserted when the output format is
                                   multi-paged.
            link_prefix:       Optional text which will be inserted before the link when the output
                                   format is multi-paged. It can be used for example to compose a
                                   list of linked subdocuments by setting it to ". ".
            multi_page_link:   True to include a link in a multi-page document (default). Otherwise
                                   the separate document is generated but not linked from here.

        Returns:
            AsciiDoc text to include in the document.
        """

        file_path = Path(file_name)
        if not file_path.is_absolute():
            file_path = (self._current_file.parent / file_path).resolve()

        if not file_path.is_file():
            raise IncludeFileNotFoundError(file_name)

        sub_context = self._context.sub_context()
        if self._context.preprocessing_run:
            sub_context.current_document = DocumentTreeNode(file_path,
                                                            self._context.current_document)
            self._context.current_document.children.append(sub_context.current_document)
        else:
            sub_context.current_document = self._context.current_document.find_child(file_path)
            assert sub_context.current_document is not None

        out_file = _process_adoc(file_path, sub_context)
        if multi_page:
            if multi_page_link:
                referenced_file = _relative_path(self._current_file, file_path)
                return (f"{link_prefix}"
                        f"<<{referenced_file}#,{link_text if link_text else referenced_file}>>")
            else:
                return ("")

        rel_path = out_file.relative_to(self._current_file.parent)
        return f"include::{rel_path}[leveloffset={leveloffset}]"

    def language(self, lang: Optional[str]) -> str:
        """Set the default language for all following commands.

        Elements will then only be inserted for that language, and other languages are ignored. The
        language can still be overridden with the `lang` keyword. Files included after this command
        will also be affected.

        Params:
            lang The new default language, or None to reset.
        """
        self._context.language = safe_language_tag(lang)

        # Prevent output of None
        return ""

    def namespace(self, namespace: Optional[str]) -> str:
        """Set the namespace to start searching for elements for all following commands.

        If the element cannot be found in this namespace, it is also searched as a fully qualified
        name. Files included after this command will also be affected.

        Args:
            namespace: The namespace to search, or None to reset. The namespace should use the
                           language specific namespace separator and should also include the
                           separator between the namespace and the short name.
        """
        self._context.namespace = namespace

        # Prevent output of None
        return ""

    def _template(self, lang: str, kind: str) -> Template:
        key = Api.TemplateKey(lang, kind)
        template = self._template_cache.get(key, None)
        if template is None:
            templates_path = templates.__path__  # type: ignore  # mypy issue #1422
            lookup = TemplateLookup(directories=templates_path + [self._context.base_dir],
                                    input_encoding="utf-8")
            try:
                template = lookup.get_template(f"{lang}/{kind}.mako")
                self._template_cache[key] = template
            except TopLevelLookupException:
                raise TemplateMissingError(lang, kind)
        return template


def process_adoc(in_file: Path,
                 build_dir: Path,
                 xml_dirs: Collection[Path],
                 debug: bool = False,
                 force_language: Optional[str] = None):
    """Process an AsciiDoc file and insert API reference.

    Args:
        in_file:        AsciiDoc file to process.
        build_dir:      Directory to store build artifacts in.
        xml_dirs:       List of directories containing Doxygen XML files.
        debug:          True to store debug information.
        force_language: Force language used when parsing doxygen XML files.

    Returns:
        Dictionary that maps input AsciiDoc files to output AsciiDoc files with inserted API
            reference.
    """

    parser = DoxygenXmlParser(force_language=force_language)

    logger.info("Loading API reference")
    for xml_dir in xml_dirs:
        for xml_file in xml_dir.glob("**/*.xml"):
            parser.parse(xml_file)
    parser.resolve_references()

    context = Context(base_dir=in_file.parent,
                      build_dir=build_dir,
                      fragment_dir=build_dir / "fragments",
                      reference=parser.api_reference,
                      current_document=DocumentTreeNode(in_file, None))
    context.reference = parser.api_reference

    context.build_dir.mkdir(parents=True, exist_ok=True)
    context.fragment_dir.mkdir(parents=True, exist_ok=True)

    try:
        _process_adoc(in_file, context)
        context.linked = []
        context.preprocessing_run = False
        context.in_to_out_file_map[in_file] = _process_adoc(in_file, context)
        _check_links(context)
        return context.in_to_out_file_map
    finally:
        if debug:
            logger.info("Writing debug data, sorry for the delay!")
            with (context.build_dir / "debug.json").open("w", encoding="utf-8") as f:
                json.dump(context.reference.elements, f, default=json_repr, indent=2)


def _process_adoc(in_file: Path, context: Context):
    logger.info(f"Processing {in_file}")
    api = Api(in_file, context)
    out_file = _out_file_name(in_file)

    template = Template(filename=os.fspath(in_file), input_encoding="utf-8")
    if context.preprocessing_run:
        context.in_to_out_file_map[in_file] = out_file

    rendered_doc = template.render(api=api)

    if not context.preprocessing_run:
        with out_file.open("w", encoding="utf-8") as f:
            print(rendered_doc, file=f)
            if multi_page:
                nav_bar = navigation_bar(context.current_document)
                if nav_bar:
                    print(nav_bar, file=f)

    return out_file


def _check_links(context: Context):
    linked = {e.id for e in context.linked}
    dangling = linked - context.inserted.keys()
    if dangling:
        names = {f"{e.language}: {e.full_name}" for e in context.linked if e.id in dangling}
        msg = ("The following elements are linked to, but not included in the documentation:\n\t" +
               "\n\t".join(names))
        if warnings_are_errors:
            raise ConsistencyError(msg)
        else:
            logger.warning(msg)


def _out_file_name(in_file: Path) -> Path:
    return in_file.parent / f".asciidoxy.{in_file.name}"


def _relative_path(from_file: Path, to_file: Path):
    assert from_file.is_absolute()
    assert to_file.is_absolute()

    path = Path()
    for ancestor in from_file.parents:
        try:
            path = path / to_file.relative_to(ancestor)
            break
        except ValueError:
            path = path / '..'

    return path


def navigation_bar(doc: DocumentTreeNode) -> str:
    next_doc: DocumentTreeNode = doc.preorder_traversal_next()
    prev_doc: DocumentTreeNode = doc.preorder_traversal_prev()

    # Don't generate navigation bar for single page documents
    if next_doc is None and prev_doc is None:
        return ""

    up_doc: Optional[DocumentTreeNode] = doc.parent
    root_doc: DocumentTreeNode = doc.root()

    def _xref_string(referencing_file: Path, doc: Optional[DocumentTreeNode], link_text: str):
        if doc is None:
            return ""
        return f"<<{_relative_path(referencing_file, doc.in_file)}#,{link_text}>>"

    home_row = f" +\n{_xref_string(doc.in_file, root_doc, 'Home')}" if root_doc != doc else ''
    return (f"""[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|{_xref_string(doc.in_file, prev_doc, 'Prev')}

|{_xref_string(doc.in_file, up_doc, 'Up')}{home_row}

|{_xref_string(doc.in_file, next_doc, 'Next')}
|===""")
