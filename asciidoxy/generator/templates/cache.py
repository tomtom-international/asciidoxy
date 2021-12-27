# Copyright (C) 2019-2021, TomTom (http://tomtom.com).
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

from ...compat import importlib_resources
from ..errors import TemplateMissingError


class TemplateCache(TemplateLookup):
    """Cache for Mako templates used by AsciiDoxy.

    Supports reading templates from a custom location using the `directories` argument of the
    constructor. If templates are not found in the custom location, the internal package resources
    of AsciiDoxy are searched.

    By default file system checks for changes to source files are disabled.
    """
    def __init__(self, custom_template_dir: Optional[Path] = None, *args, **kwargs):
        if custom_template_dir is not None:
            kwargs["directories"] = [str(custom_template_dir)]
        if "filesystem_checks" not in kwargs:
            kwargs["filesystem_checks"] = False

        super().__init__(*args, **kwargs)

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
                template = Template(text=source.read_text(encoding="UTF-8"), lookup=self)
                self.put_template(uri, template)
                return template
            else:
                raise
