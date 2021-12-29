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
"""Cache implementation for Mako templates supporting package resources."""

from pathlib import Path
from typing import Optional

from mako.exceptions import TopLevelLookupException
from mako.lookup import TemplateLookup
from mako.template import Template

import asciidoxy.generator.templates

from ..compat import importlib_resources
from ..document import Document
from .errors import TemplateMissingError


class BaseCache(TemplateLookup):
    def __init__(self, cache_name: str, cache_dir: Optional[Path] = None, *args, **kwargs):
        if cache_dir is not None:
            named_cache_dir = cache_dir / cache_name
            named_cache_dir.mkdir(parents=True, exist_ok=True)
            kwargs["module_directory"] = str(named_cache_dir)
        if "filesystem_checks" not in kwargs:
            kwargs["filesystem_checks"] = False
        if "input_encoding" not in kwargs:
            kwargs["input_encoding"] = "utf-8"

        super().__init__(*args, **kwargs)


class DocumentCache(BaseCache):
    """Cache for input documents."""
    def __init__(self, cache_dir: Optional[Path] = None, *args, **kwargs):
        super().__init__("documents", cache_dir, *args, **kwargs)

    def get_document(self, document: Document) -> Template:
        return self.get_template(str(document.original_file))

    def get_template(self, uri: str) -> Template:
        try:
            return super().get_template(uri)

        except TopLevelLookupException:
            template = Template(uri=uri, filename=uri, lookup=self, **self.template_args)
            self.put_template(uri, template)
            return template


class TemplateCache(BaseCache):
    """Cache for Mako templates used by AsciiDoxy.

    Supports reading templates from a custom location using the `directories` argument of the
    constructor. If templates are not found in the custom location, the internal package resources
    of AsciiDoxy are searched.

    By default file system checks for changes to source files are disabled.
    """
    def __init__(self,
                 custom_template_dir: Optional[Path] = None,
                 cache_dir: Optional[Path] = None,
                 *args,
                 **kwargs):
        if custom_template_dir is not None:
            kwargs["directories"] = [str(custom_template_dir)]

        super().__init__("templates", cache_dir, *args, **kwargs)

    def template_for(self, lang: str, kind: str) -> Template:
        try:
            return self.get_template(f"{lang}/{kind}.mako")
        except TopLevelLookupException:
            raise TemplateMissingError(lang, kind)

    def get_template(self, uri: str) -> Template:
        if uri.startswith("/"):
            uri = uri[1:]
        try:
            return super().get_template(uri)

        except TopLevelLookupException:
            source = importlib_resources.files(asciidoxy.generator.templates).joinpath(uri)
            if source.is_file():
                with importlib_resources.as_file(source) as source_file:
                    template = Template(uri=uri,
                                        filename=str(source_file),
                                        lookup=self,
                                        **self.template_args)
                self.put_template(uri, template)
                return template
            else:
                raise
