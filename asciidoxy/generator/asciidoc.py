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
import logging
import os

from mako.exceptions import TopLevelLookupException
from mako.lookup import TemplateLookup
from mako.template import Template
from pathlib import Path
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from typing import MutableMapping, NamedTuple, Optional

from tqdm import tqdm

from .. import templates
from ..api_reference import AmbiguousLookupError, ApiReference
from ..doxygenparser import safe_language_tag
from ..model import ReferableElement
from .._version import __version__
from .context import Context
from .errors import (AmbiguousReferenceError, ConsistencyError, IncludeFileNotFoundError,
                     IncompatibleVersionError, ReferenceNotFoundError, TemplateMissingError,
                     UnlinkableError)
from .filters import FilterSpec, InsertionFilter
from .navigation import DocumentTreeNode, navigation_bar, relative_path

logger = logging.getLogger(__name__)


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

    def filter(self,
               *,
               members: Optional[FilterSpec] = None,
               inner_classes: Optional[FilterSpec] = None,
               enum_values: Optional[FilterSpec] = None,
               exceptions: Optional[FilterSpec] = None) -> str:
        """Set a default filter used when inserting API reference documentation.

        The filter controls which members of an element are inserted. Only the members matching the
        filter are inserted, the others are ignored. Depending on the exact type of element
        inserted, its members, inner classes, enum values and/or exceptions can be filtered.

        A filter specification is either a single string, a list of strings, or a dictionary.

        A single string is the same as a list of strings with just one item.

        A list of strings defines a set of regular expressions to be applied to the name. They are
        applied in the order they are specified. If the element is still included after all filters
        have been applied, it is inserted.

        Each string can have the following value:

        * `NONE`: Exclude all elements.
        * `ALL`: Include all elements.
        * `<regular expression>` or `+<regular expression`: Include elements that match the regular
          expression.
        * `-<regular expression>`: Exclude elements that match the regular expression.

        If the first string is an include regular expression, an implicit `NONE` is prepended, if
        the first string is an exclude regular expression, an implicit `ALL` is prepended.

        Some filters support filtering on other properties than the name. By default they only
        filter on the name. To filter the other properties use a dictionary, where the key is the
        name of the property, and the value is a string or list of strings with the filter.

        Args:
            members:       Filter to apply to members of a compound. Supports filtering on `name`,
                               `kind`, and `prot`ection level.
            inner_classes: Filter to apply to inner classes of a compound. Supports filtering on
                               `name` and `kind`.
            enum_values:   Filter to apply to enum values of a compound or member. Supports
                               filtering on `name` only.
            exceptions:    Filter to apply to exceptions thrown by a member. Supports filtering on
                               the `name` of the exception type only.

        Returns:
            An empty string.
        """
        self._context.insert_filter = InsertionFilter(members, inner_classes, enum_values,
                                                      exceptions)
        return ""

    def insert(self,
               name: str,
               *,
               kind: Optional[str] = None,
               lang: Optional[str] = None,
               members: Optional[FilterSpec] = None,
               inner_classes: Optional[FilterSpec] = None,
               enum_values: Optional[FilterSpec] = None,
               exceptions: Optional[FilterSpec] = None,
               ignore_global_filter: bool = False,
               leveloffset: str = "+1",
               **asciidoc_options) -> str:
        """Insert API reference documentation.

        Only `name` is mandatory. Multiple names may match the same name. Use `kind` and `lang` to
        disambiguate.

        For the supported format of the filter arguments see `Api.filter()`.

        Args:
            name:                 Fully qualified name of the object to insert.
            kind:                 Kind of object to generate reference documentation for.
            lang:                 Programming language of the object.
            members:              Filter to apply to members of a compound. Supports filtering on
                                      `name`, `kind`, and `prot`ection level.
            inner_classes:        Filter to apply to inner classes of a compound. Supports
                                      filtering on `name` and `kind`.
            enum_values:          Filter to apply to enum values of a compound or member. Supports
                                      filtering on `name` only.
            exceptions:           Filter to apply to exceptions thrown by a member. Supports
                                      filtering on the `name` of the exception type only.
            ignore_global_filter: True to ignore the global filter set with `Api.filter()`. False
                                      to apply the filters on top of the global filter.
            leveloffset:          Offset of the top header of the inserted text from the top level
                                      header of the including document.
            asciidoc_options:     Any additional option is added as an attribute to the include
                                      directive in single page mode.

        Returns:
            AsciiDoc text to include in the document.
        """
        if ignore_global_filter:
            insert_filter = InsertionFilter(members, inner_classes, enum_values, exceptions)
        elif (members is not None or inner_classes is not None or enum_values is not None
              or exceptions is not None):
            insert_filter = self._context.insert_filter.extend(members, inner_classes, enum_values,
                                                               exceptions)
        else:
            insert_filter = self._context.insert_filter

        return self.insert_fragment(self.find_element(name, kind=kind, lang=lang), insert_filter,
                                    leveloffset, **asciidoc_options)

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
            if self._context.warnings_are_errors:
                raise
            else:
                logger.warning(str(ref_not_found))
                return text or name

        if element.id is None:
            unlinkable = UnlinkableError(name, lang=lang, kind=kind)
            if self._context.warnings_are_errors:
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
                if self._context.warnings_are_errors:
                    raise ConsistencyError(msg)
                else:
                    logger.warning(msg)

        if not self._context.multi_page:
            file_path = Path(file_name)
            if not file_path.is_absolute():
                file_path = (self._current_file.parent / file_path).resolve().relative_to(
                    self._context.base_dir)
            referenced_file_name = _out_file_name(file_path)
        return (f"<<{referenced_file_name}#{anchor},"
                f"{link_text if link_text is not None else anchor}>>")

    def insert_fragment(self,
                        element,
                        insert_filter: InsertionFilter,
                        leveloffset: str = "+1",
                        kind_override: Optional[str] = None,
                        **asciidoc_options) -> str:
        """Generate and insert a documentation fragment.

        Args:
            element:          Python representation of the element to insert.
            insertion_filter: Filter for members to insert.
            leveloffset:      Offset of the top header of the inserted text from the top level
                                  header of the including document.
            kind_override:    Override the kind of template to use. None to use the kind of
                                  `element`.
            asciidoc_options: Any additional option is added as an attribute to the include
                                  directive in single page mode.

        Returns:
            AsciiDoc text to include in the document.
        """

        assert element.id
        fragment_file = self._context.fragment_dir / f"{element.id}.adoc"

        if kind_override is None:
            kind = element.kind
        else:
            kind = kind_override

        rendered_doc = self._template(element.language, kind).render(element=element,
                                                                     insert_filter=insert_filter,
                                                                     api_context=self._context,
                                                                     api=self)

        if not self._context.preprocessing_run:
            with fragment_file.open("w", encoding="utf-8") as f:
                print(rendered_doc, file=f)

        asciidoc_options["leveloffset"] = leveloffset
        attributes = ",".join(f"{str(key)}={str(value)}" for key, value in asciidoc_options.items())
        return f"include::{fragment_file}[{attributes}]"

    def include(self,
                file_name: str,
                leveloffset: str = "+1",
                link_text: str = "",
                link_prefix: str = "",
                multi_page_link: bool = True,
                **asciidoc_options) -> str:
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
            asciidoc_options:  Any additional option is added as an attribute to the include
                                   directive in single page mode.

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
        if self._context.multi_page:
            if multi_page_link:
                referenced_file = relative_path(self._current_file, file_path)
                return (f"{link_prefix}"
                        f"<<{referenced_file}#,{link_text if link_text else referenced_file}>>")
            else:
                return ""

        asciidoc_options["leveloffset"] = leveloffset
        attributes = ",".join(f"{str(key)}={str(value)}" for key, value in asciidoc_options.items())

        rel_path = out_file.relative_to(self._current_file.parent)
        return f"include::{rel_path}[{attributes}]"

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

    def require_version(self, specifier: str) -> str:
        """Require a specific version of AsciiDoxy.

        If the running version of AsciiDoxy does not match, an exception is thrown and generation
        stops.

        Args:
            specifier: One or more comma-separated version specifiers matching the PEP 440
            standard.
        """
        spec = SpecifierSet(specifier)

        if not Version(__version__) in spec:
            raise IncompatibleVersionError(specifier)

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
                 api_reference: ApiReference,
                 warnings_are_errors: bool = False,
                 multi_page: bool = False,
                 progress: Optional[tqdm] = None):
    """Process an AsciiDoc file and insert API reference.

    Args:
        in_file:             AsciiDoc file to process.
        build_dir:           Directory to store build artifacts in.
        api_reference:       API reference to insert in the documents.
        warnings_are_errors: True to treat every warning as an error.
        multi_page:          True to enable multi page output.

    Returns:
        Dictionary that maps input AsciiDoc files to output AsciiDoc files with inserted API
            reference.
    """

    context = Context(base_dir=in_file.parent,
                      build_dir=build_dir,
                      fragment_dir=build_dir / "fragments",
                      reference=api_reference,
                      current_document=DocumentTreeNode(in_file, None))

    context.build_dir.mkdir(parents=True, exist_ok=True)
    context.fragment_dir.mkdir(parents=True, exist_ok=True)

    context.warnings_are_errors = warnings_are_errors
    context.multi_page = multi_page
    context.progress = progress

    _process_adoc(in_file, context)
    context.linked = []
    context.preprocessing_run = False
    context.in_to_out_file_map[in_file] = _process_adoc(in_file, context)
    _check_links(context)
    return context.in_to_out_file_map


def _process_adoc(in_file: Path, context: Context):
    logger.info(f"Processing {in_file}")
    api = Api(in_file, context)
    out_file = _out_file_name(in_file)

    template = Template(filename=os.fspath(in_file), input_encoding="utf-8")
    if context.preprocessing_run:
        context.in_to_out_file_map[in_file] = out_file

        if context.progress is not None:
            context.progress.total = 2 * len(context.in_to_out_file_map)
            context.progress.update(0)

    rendered_doc = template.render(api=api)

    if not context.preprocessing_run:
        with out_file.open("w", encoding="utf-8") as f:
            print(rendered_doc, file=f)
            if context.multi_page:
                nav_bar = navigation_bar(context.current_document)
                if nav_bar:
                    print(nav_bar, file=f)

    if context.progress is not None:
        context.progress.update()

    return out_file


def _check_links(context: Context):
    linked = {e.id for e in context.linked}
    dangling = linked - context.inserted.keys()
    if dangling:
        names = {f"{e.language}: {e.full_name}" for e in context.linked if e.id in dangling}
        msg = ("The following elements are linked to, but not included in the documentation:\n\t" +
               "\n\t".join(names))
        if context.warnings_are_errors:
            raise ConsistencyError(msg)
        else:
            logger.warning(msg)


def _out_file_name(in_file: Path) -> Path:
    return in_file.parent / f".asciidoxy.{in_file.name}"
