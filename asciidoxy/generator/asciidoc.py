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
"""Generation of AsciiDoc output."""

import functools
import inspect
import logging
import warnings
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    List,
    MutableMapping,
    NamedTuple,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
)

from mako.template import Template
from tqdm import tqdm

import asciidoxy.generator
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .._version import __version__
from ..api_reference import AmbiguousLookupError, ApiReference
from ..compat import importlib_resources
from ..config import Configuration
from ..document import Document
from ..model import ReferableElement
from ..packaging import PackageManager, UnknownFileError, UnknownPackageError
from ..parser.doxygen import safe_language_tag
from ..path_utils import relative_path
from ..transcoder import TranscoderBase
from .context import Context, stacktrace
from .errors import (
    AmbiguousReferenceError,
    ConsistencyError,
    DuplicateIncludeError,
    IncludeFileNotFoundError,
    IncompatibleVersionError,
    InvalidApiCallError,
    MissingPackageError,
    MissingPackageFileError,
    ReferenceNotFoundError,
    UnknownAnchorError,
    UnlinkableError,
)
from .filters import FilterSpec, InsertionFilter
from .navigation import multipage_toc, navigation_bar

logger = logging.getLogger(__name__)

SUPPORTED_COMMANDS = [
    "cross_document_ref",
    "filter",
    "include",
    "insert",
    "language",
    "link",
    "multipage_toc",
    "namespace",
    "require_version",
    "anchor",
]

_WrappedFunc = TypeVar("_WrappedFunc", bound=Callable[..., Any])


def _arg_to_str(arg: Optional[Any]) -> str:
    if arg is None:
        return "None"
    if isinstance(arg, ReferableElement):
        return f"'{arg.full_name}'"
    return repr(arg)


def _format_action(name: str, args, kwargs, show_args, show_kwargs) -> str:
    # Using index + 1 because self is removed from args
    args_parts = [_arg_to_str(value) for index, value in enumerate(args) if index + 1 in show_args]
    kwargs_parts = [
        f"{key}={_arg_to_str(value)}" for key, value in kwargs.items() if key in show_kwargs
    ]
    return f"{name}({', '.join(args_parts + kwargs_parts)})"


def _lookup_args(f: _WrappedFunc, show_args: Sequence[Union[str, int]]):
    signature = inspect.signature(f)
    param_names = list(signature.parameters.keys())
    arg_indices = []
    kwarg_names = []
    for arg in show_args:
        if isinstance(arg, str):
            arg_indices.append(param_names.index(arg))
            kwarg_names.append(arg)
        elif isinstance(arg, int):
            arg_indices.append(arg)
            kwarg_names.append(param_names[arg])
    return arg_indices, kwarg_names


def _stackframe(original_function: Optional[_WrappedFunc] = None,
                *,
                name: Optional[str] = None,
                show_args: Sequence[Union[int, str]] = (1, ),
                internal: bool = False,
                _name: Callable[..., str],
                _context: Callable[..., Context],
                _api: Callable[..., "Api"],
                _other_self=None):
    def _decorator(f: _WrappedFunc) -> _WrappedFunc:
        arg_indices, kwarg_names = _lookup_args(f, show_args)

        @wraps(f)
        def _wrapper(*args, **kwargs):
            _self = _other_self or args[0]
            _context(_self).push_stack(
                _format_action(_name(f), args[1:], kwargs, arg_indices, kwarg_names),
                document=_api(_self)._context.document if not internal else None,
                package=_api(_self)._context.document.package.name,
                internal=internal)
            ret = f(*args, **kwargs)
            _context(_self).pop_stack()
            return ret

        return cast(_WrappedFunc, _wrapper)

    if original_function is not None:
        return _decorator(original_function)
    return _decorator


def _api_stackframe(*args, name: Optional[str] = None, **kwargs):
    def _name(f: _WrappedFunc) -> str:
        return name or f.__name__

    def _context(self) -> Context:
        return self._context

    def _api(self) -> "Api":
        return self

    return _stackframe(*args, name=name, _name=_name, _context=_context, _api=_api, **kwargs)


def _proxy_stackframe(*args, name: Optional[str] = None, **kwargs):
    def _name(f: _WrappedFunc) -> str:
        return name or f"api.{f.__name__}"

    def _context(self) -> Context:
        return self._api._context

    def _api(self) -> "Api":
        return self._api

    return _stackframe(*args, name=name, _name=_name, _context=_context, _api=_api, **kwargs)


class Api(ABC):
    """Methods to insert and link to API reference documentation from AsciiDoc files."""
    class TemplateKey(NamedTuple):
        lang: str
        kind: str

    _template_cache: MutableMapping[TemplateKey, Template] = {}

    _context: Context

    def __init__(self, context: Context):
        assert context.package_manager.work_dir.is_dir()
        assert context.reference is not None

        self._context = context

    def filter(self,
               *,
               members: Optional[FilterSpec] = None,
               exceptions: Optional[FilterSpec] = None) -> str:
        """Set a default filter used when inserting API reference documentation.

        The filter controls which members of an element are inserted. Only the members matching the
        filter are inserted, the others are ignored. Depending on the exact type of element
        inserted, its members and/or exceptions can be filtered.

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
            exceptions:    Filter to apply to exceptions thrown by a member. Supports filtering on
                               the `name` of the exception type only.

        Returns:
            An empty string.
        """
        self._context.insert_filter = InsertionFilter(members, exceptions)
        return ""

    @_api_stackframe
    def insert(self,
               name: str,
               *,
               kind: Optional[str] = None,
               lang: Optional[str] = None,
               members: Optional[FilterSpec] = None,
               exceptions: Optional[FilterSpec] = None,
               ignore_global_filter: bool = False,
               allow_overloads: bool = False,
               leveloffset: str = "+1",
               template: Optional[str] = None) -> str:
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
            exceptions:           Filter to apply to exceptions thrown by a member. Supports
                                      filtering on the `name` of the exception type only.
            ignore_global_filter: True to ignore the global filter set with `Api.filter()`. False
                                      to apply the filters on top of the global filter.
            allow_overloads:      Insert first match in an overload set. Disabled by default.
            leveloffset:          Offset of the top header of the inserted text from the top level
                                      header of the including document.
            template:             *Experimental* Alternative template to use when inserting the
                                      reference documentation.

        Returns:
            AsciiDoc text to include in the document.
        """
        if ignore_global_filter:
            insert_filter = InsertionFilter(members, exceptions)
        elif (members is not None or exceptions is not None):
            insert_filter = self._context.insert_filter.extend(members, exceptions)
        else:
            insert_filter = self._context.insert_filter

        return self.insert_fragment(self.find_element(name,
                                                      kind=kind,
                                                      lang=lang,
                                                      allow_overloads=allow_overloads),
                                    insert_filter,
                                    leveloffset,
                                    kind_override=template)

    @_api_stackframe
    def link(self,
             name: str,
             *,
             kind: Optional[str] = None,
             lang: Optional[str] = None,
             text: Optional[str] = None,
             full_name: bool = False,
             allow_overloads: bool = True) -> str:
        """Insert a link to API reference documentation.

        Only `name` is mandatory. Multiple names may match the same name. Use `kind` and `lang` to
        disambiguate.

        Args:
            name:            Fully qualified name of the object to link to.
            kind:            Kind of object to link to.
            lang:            Programming language of the object.
            text:            Alternative text to use for the link. If not supplied, the object name
                                 is used.
            full_name:       Use the fully qualified name of the object for the link text.
            allow_overloads: Link to the first match in an overload set. Enabled by default.

        Returns:
            AsciiDoc text to include in the document.
        """
        if text is not None and full_name is True:
            raise InvalidApiCallError("`text` and `full_name` cannot be used together.")

        try:
            element = self.find_element(name, kind=kind, lang=lang, allow_overloads=allow_overloads)
        except ReferenceNotFoundError as ref_not_found:
            self._warning_or_error(ref_not_found)
            return text or name

        if element.id is None:
            self._warning_or_error(UnlinkableError(name, lang=lang, kind=kind))
            return text or name

        if text is not None:
            link_text = text
        elif full_name:
            link_text = name
        else:
            link_text = element.name

        return self.link_to_element(element.id, link_text)

    @abstractmethod
    def cross_document_ref(self,
                           file_name: Optional[str] = None,
                           *,
                           package_name: Optional[str] = None,
                           anchor: Optional[str] = None,
                           link_text: Optional[str] = None) -> str:
        """AsciiDoc cross-document reference.

        Since AsciiDoxy in multi-page mode generates intermediate AsciiDoc files and process them
        with AsciiDoctor in order to create final output document(s) the direct AsciiDoc syntax
        (i.e. `++&lt;&lt;file_name#anchor,link_text&gt;&gt;++`) doesn't work. You must use this
        method instead.

        Args:
             file_name:    Name of the file. If `package_name` is specified, it must be relative to
                              the root of the package. Otherwise, it is relative to the current
                              document. Absolute paths are not supported.
             package_name: Name of the package containing the file. If not specified, the file must
                               come from the same package.
             anchor:       Anchor to the referred section in the referred AsciiDoc document. If no
                               `file_name` or `package_name` is given it refers to a flexible
                               anchor as inserted by `anchor`.
             link_text:    Text for the link to insert. If not provided, either the anchor, the
                               title of the document or the name of the file is used.

        Returns:
            AsciiDoc cross-document reference.

        Raises:
            InvalidApiCallError:     Incorrect argument or argument combinations are used.
            MissingPackageError:     The specified package is not available.
            MissingPackageFileError: The specified file name is not available in the package.
            UnknownAnchorError:      The `anchor` is not a known flexible anchor and no `file_name`
                                         or `package_name` is provided.
        """
        ...

    @abstractmethod
    def anchor(self, name: str, *, link_text: Optional[str] = None) -> str:
        """Create a flexible anchor.

        In multi-page mode it may be hard to move content containing anchors between files. All
        references to the anchor need to be updated to point to the correct files. This command
        allows you to create flexible anchors.

        In single-page mode, this will result in a normal AsciiDoc anchor. In multi-page mode it
        will also make sure that other files can refer to the anchor without having to specify the
        file containing it.

        Args:
            name:      Name of the anchor. Use this name in `cross_document_ref` to refer to the
                           anchor.
            link_text: Optional text to use in links to the anchor.

        Returns:
            AsciiDoc anchor.

        Raises:
            DuplicateAnchorError: An anchor with the specified name already exists.
        """
        ...

    @_api_stackframe(show_args=("file_name", ))
    def include(self,
                file_name: str,
                *,
                package_name: Optional[str] = None,
                leveloffset: str = "+1",
                link_text: str = "",
                link_prefix: str = "",
                multipage_link: bool = True,
                always_embed: bool = False,
                **asciidoc_options) -> str:
        """Include another AsciiDoc file, and process it to insert API references.

        If the output format is multi-paged, the method will by default cause generation of
        separate output document for the included AsciiDoc document and optional insertion of link
        referring to the document.

        Args:
            file_name:         Name of the file. If `package_name` is specified, it must be relative
                                   to the root of the package. Otherwise, it is relative to the
                                   current document. Absolute paths are not supported.
            package_name:      Name of the package containing the file. If not specified, the file
                                   must come from the same package.
            leveloffset:       Offset of the top header of the inserted text from the top level
                                   header of the including document.
            link_text:         Text of the link which will be inserted when the output format is
                                   multi-paged. By default the document title (if found) or file
                                   name stem is used.
            link_prefix:       Optional text which will be inserted before the link when the output
                                   format is multi-paged. It can be used for example to compose a
                                   list of linked subdocuments by setting it to ". ".
            multipage_link:    True to include a link in a multipage document (default). Otherwise
                                   the separate document is generated but not linked from here.
            always_embed:      True to always embed the contents in the current document, even in
                                   multipage mode.
            asciidoc_options:  Any additional option is added as an attribute to the include
                                   directive in single page mode.

        Returns:
            AsciiDoc text to include in the document.

        Raises:
            InvalidApiCallError:     Incorrect argument or argument combinations are used.
            MissingPackageError:     The specified package is not available.
            MissingPackageFileError: The specified file name is not available in the package.
        """
        if Path(file_name).is_absolute():
            raise InvalidApiCallError("`file_name` must be a relative path.")

        doc = self._find_document(file_name, package_name)
        if doc is None:
            return ""

        sub_api = self._sub_api(doc, always_embed)
        if always_embed:
            return sub_api.render_adoc()

        sub_api.process_adoc()

        if self._context.config.multipage and not always_embed:
            if multipage_link:
                referenced_file = self._context.document.relative_path_to(doc)
                if not link_text:
                    link_text = doc.title
                return (f"{link_prefix}<<{referenced_file}#,{link_text}>>")
            else:
                return ""

        if leveloffset:
            asciidoc_options["leveloffset"] = leveloffset
        attributes = ",".join(f"{str(key)}={str(value)}" for key, value in asciidoc_options.items())

        rel_path = self._context.document.relative_path_to(doc)
        return f"[#{self._file_top_anchor(doc)}]\ninclude::{rel_path}[{attributes}]"

    def language(self, lang: Optional[str], *, source: Optional[str] = None) -> str:
        """Set the default language for all following commands.

        Elements will then only be inserted for that language, and other languages are ignored. The
        language can still be overridden with the `lang` keyword. Files included after this command
        will also be affected.

        Optionally, a different language can be used as the `source` of the API reference. If an
        element is inserted that does not exist in the target `lang`, it is automatically
        transcoded from the `source` language. This feature is only available for a limited set of
        languages.

        Params:
            lang:   The new default language, or None to reset.
            source: Language to transcode from if an element is not available in the
                        selected language. Only available for limited combinations.

        Raises:
            InvalidApiCallError: The `source` language needs to be different from `lang`, and `lang`
                                     is required when `source` is specified.
        """
        lang = safe_language_tag(lang)
        source = safe_language_tag(source)

        if source and not lang:
            raise InvalidApiCallError("When specifying `source`, `lang` cannot be empty.")
        if source and source == lang:
            raise InvalidApiCallError("`source` and `lang` cannot be the same.")

        self._context.language = lang if lang else None
        self._context.source_language = source if source else None

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

    def multipage_toc(self, side: str = "left") -> str:
        """Insert a table of contents for multipage documents.

        Only supported for the HTML backend and when multipage mode is on.

        This command needs to be included in the document headers to work. To not break headers
        when multipage mode is off, it is recommended to add it to the end of the headers.

        Args:
            side: Show the multipage TOC at the `left` or `right` side.
        """
        return ""

    # Internal, non-API methods

    def find_element(self,
                     name: str,
                     *,
                     kind: Optional[str] = None,
                     lang: Optional[str] = None,
                     allow_overloads: bool = False) -> ReferableElement:
        """Find a reference to API documentation.

        Only `name` is mandatory. Multiple names may match the same name. Use `kind` and `lang` to
        disambiguate.

        Args:
            name:            Name of the object to insert.
            kind:            Kind of object to generate reference documentation for.
            lang:            Programming language of the object.
            allow_overloads: True to return the first match of an overload set.

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
                                                   lang=lang,
                                                   allow_overloads=allow_overloads)
        except AmbiguousLookupError as ex:
            raise AmbiguousReferenceError(name, ex.candidates)

        if element is None:
            if (lang and lang == self._context.language and self._context.source_language):
                source_element = self.find_element(name,
                                                   kind=kind,
                                                   lang=self._context.source_language,
                                                   allow_overloads=allow_overloads)
                if source_element is not None:
                    return TranscoderBase.transcode(source_element, lang, self._context.reference)

            raise ReferenceNotFoundError(name, lang=lang, kind=kind)
        return element

    @abstractmethod
    def insert_fragment(self,
                        element,
                        insert_filter: InsertionFilter,
                        leveloffset: str = "+1",
                        kind_override: Optional[str] = None) -> str:
        """Generate and insert a documentation fragment.

        Args:
            element:          Python representation of the element to insert.
            insertion_filter: Filter for members to insert.
            leveloffset:      Offset of the top header of the inserted text from the top level
                                  header of the including document.
            kind_override:    Override the kind of template to use. None to use the kind of
                                  `element`.

        Returns:
            AsciiDoc text to include in the document.
        """
        ...

    def inserted(self, element: ReferableElement) -> str:
        """Register that an element has been inserted."""
        return ""

    @abstractmethod
    def link_to_element(self, element_id: str, link_text: str) -> str:
        """Insert a link to a specific element."""
        ...

    def render_adoc(self) -> str:
        """Render combined AsciiDoc from the contents of the file.

        Returns:
            Rendered AsciiDoc.
        """
        template = self._context.document_cache.get_document(self._context.document)
        return template.render(api=ApiProxy(self),
                               env=self._context.env,
                               config=self._context.config,
                               **self._commands())

    @abstractmethod
    def process_adoc(self) -> None:
        """Process the AsciiDoc file.

        Returns:
            Name of the processed output file.
        """
        ...

    # "Protected" methods

    def _find_document(self, file_name: Optional[str],
                       package_name: Optional[str]) -> Optional[Document]:
        assert file_name or package_name
        requested_package_name = package_name

        try:
            rel_file_name: Optional[Path]
            if package_name and file_name:
                rel_file_name = Path(file_name)
            elif file_name and not self._context.document.package.scoped:
                # and not package_name
                # Deprecated support for old style packages
                package_name, rel_file_name = self._context.package_manager.find_original_file(
                    (self._context.document.work_file.parent / file_name).resolve())
            elif file_name:  # and not package_name
                rel_file_name = self._context.document.resolve_relative_path(file_name)
                package_name = self._context.document.package.name
            else:  # package_name and not file_name
                rel_file_name = None
            return self._context.find_document(package_name, rel_file_name)

        except UnknownPackageError:
            assert requested_package_name
            self._warning_or_error(MissingPackageError(requested_package_name))
            return None
        except UnknownFileError:
            assert file_name
            if not requested_package_name:
                self._warning_or_error(IncludeFileNotFoundError(file_name))
            else:
                self._warning_or_error(MissingPackageFileError(requested_package_name, file_name))
            return None

    def _warning_or_error(self, error: Exception):
        if self._context.config.warnings_are_errors:
            raise error
        else:
            logger.warning(str(error))

    def _sub_api(self, document: Document, embedded: bool = False) -> "Api":
        return self.__class__(self._context.sub_context(document))

    def _render(self,
                element,
                insert_filter: InsertionFilter,
                kind_override: Optional[str] = None,
                leveloffset: int = 1) -> str:
        assert element.id
        assert element.language

        if kind_override is None:
            kind = element.kind
        else:
            kind = kind_override

        template = self._context.templates.template_for(element.language, kind)
        return template.render(element=element,
                               insert_filter=insert_filter,
                               api_context=self._context,
                               api=self,
                               leveloffset=leveloffset,
                               **self._commands())

    def _file_top_anchor(self, doc: Document) -> str:
        return "top-" + "-".join(doc.relative_path.with_suffix("").parts) + "-top"

    def _commands(self):
        return {name: getattr(self, name) for name in SUPPORTED_COMMANDS}


class PreprocessingApi(Api):
    def _sub_api(self, document: Document, embedded: bool = False) -> "Api":
        sub_context = self._context.sub_context(document)

        if document.is_included or (not embedded and document.is_embedded):
            self._warning_or_error(DuplicateIncludeError(document, embedded))

        if embedded:
            self._context.document.embed(document)
        else:
            self._context.document.include(document)

        return self.__class__(sub_context)

    @_api_stackframe(name="insert", show_args=("element", ), internal=True)
    def insert_fragment(self,
                        element,
                        insert_filter: InsertionFilter,
                        leveloffset: Union[str, int] = "+1",
                        kind_override: Optional[str] = None) -> str:
        self._render(element, insert_filter, kind_override)
        return ""

    def inserted(self, element: ReferableElement) -> str:
        self._context.insert(element)
        return ""

    @_api_stackframe(name="link", show_args=("link_text", ), internal=True)
    def link_to_element(self, element_id: str, link_text: str) -> str:
        self._context.link_to_element(element_id)
        return ""

    def process_adoc(self):
        logger.info(f"Preprocessing {self._context.document}")

        if self._context.progress is not None:
            self._context.progress.total = 2 * len(self._context.documents)
            self._context.progress.update(0)

        self.render_adoc()

        if self._context.progress is not None:
            self._context.progress.update()

    def cross_document_ref(self,
                           file_name: Optional[str] = None,
                           *,
                           package_name: Optional[str] = None,
                           anchor: Optional[str] = None,
                           link_text: Optional[str] = None) -> str:
        if not file_name and not package_name and not anchor:
            raise InvalidApiCallError("At least `file_name`, `package_name`, or `anchor` is "
                                      "required.")
        if file_name and Path(file_name).is_absolute():
            raise InvalidApiCallError("`file_name` must be a relative path.")

        if file_name or package_name:
            # Only check the existance of the file in the correct package
            self._find_document(file_name, package_name)
        return ""

    def anchor(self, name: str, *, link_text: Optional[str] = None) -> str:
        if not name:
            raise InvalidApiCallError("`name` cannot be empty.")
        self._context.register_anchor(name, link_text)
        return ""


class GeneratingApi(Api):
    def multipage_toc(self, side: str = "left") -> str:
        if not self._context.config.multipage:
            return ""

        toc_content = multipage_toc(self._context.output_document, side)
        with self._context.docinfo_footer_file().open(mode="w", encoding="utf-8") as f:
            f.write(toc_content)
        self._context.output_document.stylesheet = f"asciidoxy-toc-{side}.css"
        stylesheet_rel_path = relative_path(self._context.output_document.work_file,
                                            self._context.output_document.stylesheet_file)
        return f":docinfo: private\n:stylesheet: {stylesheet_rel_path}"

    def cross_document_ref(self,
                           file_name: Optional[str] = None,
                           *,
                           package_name: Optional[str] = None,
                           anchor: Optional[str] = None,
                           link_text: Optional[str] = None) -> str:

        if file_name and Path(file_name).is_absolute():
            raise InvalidApiCallError("`file_name` must be a relative path.")

        if file_name or package_name:
            document = self._find_document(file_name, package_name)
            if document is None:
                return ""

            if not document.is_used:
                msg = (f"Invalid cross-reference from document '{self._context.document}' "
                       f"to document: '{file_name}'. The referenced document: {document} "
                       f"is not included anywhere across the whole documentation tree.")
                self._warning_or_error(ConsistencyError(msg))
                return ""

            if not anchor and not link_text:
                link_text = document.title
            elif not link_text:
                link_text = anchor

            if not anchor:
                if not self._context.config.multipage:
                    anchor = self._file_top_anchor(document)
                else:
                    anchor = ""

            link_file_path = self._context.link_to_document(document)

        elif anchor:
            # Flexible anchor
            try:
                link_file_path, default_link_text = self._context.link_to_anchor(anchor)
            except UnknownAnchorError as ex:
                self._warning_or_error(ex)
                link_file_path = self._context.link_to_document(self._context.document)
                default_link_text = None

            link_text = link_text or default_link_text or anchor

        else:
            raise InvalidApiCallError("At least `file_name`, `package_name`, or `anchor` is "
                                      "required.")

        return (f"<<{link_file_path}#{anchor},{link_text}>>")

    def anchor(self, name: str, *, link_text: Optional[str] = None) -> str:
        if link_text:
            return f"[#{name},reftext='{link_text}']"
        else:
            return f"[#{name}]"

    @_api_stackframe(name="insert", show_args=("element", ), internal=True)
    def insert_fragment(self,
                        element,
                        insert_filter: InsertionFilter,
                        leveloffset: Union[str, int] = "+1",
                        kind_override: Optional[str] = None) -> str:
        return self._render(element, insert_filter, kind_override, int(leveloffset))

    @_api_stackframe(name="link", show_args=("link_text", ), internal=True)
    def link_to_element(self, element_id: str, link_text: str) -> str:
        containing_doc = self._context.file_with_element(element_id)
        if containing_doc is not None:
            file_part = f"{self._context.document.relative_path_to(containing_doc)}#"
        else:
            file_part = ""

        return f"xref:{file_part}{element_id}[++{link_text}++]"

    def process_adoc(self):
        logger.info(f"Processing {self._context.document}")
        self._context.linked = []

        rendered_doc = self.render_adoc()

        with self._context.document.work_file.open("w", encoding="utf-8") as f:
            print(rendered_doc, file=f)
            if self._context.config.multipage and not self._context.document.is_embedded:
                nav_bar = navigation_bar(self._context.document)
                if nav_bar:
                    print(nav_bar, file=f)

        self._copy_stylesheet()

        if self._context.progress is not None:
            self._context.progress.update()

    def _copy_stylesheet(self):
        if self._context.document.stylesheet is None:
            self._context.document.stylesheet = "asciidoxy-no-toc.css"
        css_source_file = importlib_resources.files(asciidoxy.generator).joinpath(
            self._context.document.stylesheet)
        assert css_source_file.is_file()
        self._context.document.stylesheet_file.write_text(
            css_source_file.read_text(encoding="utf-8"), encoding="utf-8")


class ApiProxy:
    """Proxy for exposing legacy `api.` commands."""
    _api: Api

    def __init__(self, api: Api):
        self._api = api

    def __getattr__(self, name: str):
        warnings.warn("Using the api. prefix is deprecated and will be removed in 0.9.0.",
                      FutureWarning)

        if name in ("link", "insert"):
            return _proxy_stackframe(getattr(self._api, name), name=f"api.{name}", _other_self=self)
        elif name in SUPPORTED_COMMANDS:
            return getattr(self._api, name)
        elif name.startswith("insert_"):
            return _proxy_stackframe(functools.partial(self._api.insert, kind=name[7:]),
                                     name=f"api.{name}",
                                     _other_self=self)
        elif name.startswith("link_"):
            return _proxy_stackframe(functools.partial(self._api.link, kind=name[5:]),
                                     name=f"api.{name}",
                                     _other_self=self)
        else:
            raise AttributeError(name)

    def cross_document_ref(self,
                           file_name: Optional[str] = None,
                           anchor: Optional[str] = None,
                           link_text: Optional[str] = None) -> str:
        warnings.warn("Using the api. prefix is deprecated and will be removed in 0.9.0.",
                      FutureWarning)

        return self._api.cross_document_ref(file_name, anchor=anchor, link_text=link_text)

    @_proxy_stackframe
    def include(self,
                file_name: str,
                leveloffset: str = "+1",
                link_text: str = "",
                link_prefix: str = "",
                multipage_link: bool = True,
                always_embed: bool = False,
                **asciidoc_options) -> str:
        warnings.warn("Using the api. prefix is deprecated and will be removed in 0.9.0.",
                      FutureWarning)

        return self._api.include(file_name,
                                 leveloffset=leveloffset,
                                 link_text=link_text,
                                 link_prefix=link_prefix,
                                 multipage_link=multipage_link,
                                 always_embed=always_embed,
                                 **asciidoc_options)


def process_adoc(doc: Document,
                 api_reference: ApiReference,
                 package_manager: PackageManager,
                 config: Configuration,
                 progress: Optional[tqdm] = None) -> List[Document]:
    """Process an AsciiDoc file and execute all embedded python code.

    Args:
        doc:                 AsciiDoc file to process.
        api_reference:       API reference to insert in the documents.
        package_manager:     Reference to the package manager to get additional files from.
        config:              Configuration from the command line arguments.
        progress:            Optional progress reporting widget.

    Returns:
        Dictionary that maps input AsciiDoc files to output AsciiDoc files with inserted API
            reference.
    """

    doc.is_root = True
    context = Context(reference=api_reference,
                      package_manager=package_manager,
                      document=doc,
                      config=config)

    context.progress = progress

    PreprocessingApi(context).process_adoc()
    _check_links(context)
    GeneratingApi(context).process_adoc()
    return list(context.documents.values())


def _check_links(context: Context):
    dangling = context.linked.keys() - context.inserted.keys()
    if dangling:
        messages = []
        for element_id in dangling:
            element = context.reference.find(target_id=element_id)
            if element is None:
                raise RuntimeError(f"Internal consistency error: unknown element id: {element_id}."
                                   " Please file a bug report.")

            traces = '\n'.join(stacktrace(t) for t in context.linked[element_id])
            messages.append(f"{element.language}: {element.full_name} not included in"
                            f" documentation, but linked here:\n{traces}")

        if context.config.warnings_are_errors:
            raise ConsistencyError("\n".join(messages))
        else:
            logger.warning("\n".join(messages))
