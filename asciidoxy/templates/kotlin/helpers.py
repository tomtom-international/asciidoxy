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
"""Helper functions for Kotlin templates."""

from typing import Iterator

from asciidoxy.model import Member, Parameter
from asciidoxy.templates.helpers import TemplateHelper


class KotlinTemplateHelper(TemplateHelper):
    def public_constants(self) -> Iterator[Member]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if (m.kind == "variable" and m.prot == "public" and m.returns and m.returns.type
                    and m.returns.type.prefix and "final" in m.returns.type.prefix))

    def parameter(self, param: Parameter, *, link: bool = True, default_value: bool = False) -> str:
        if default_value and param.default_value:
            defval = f" = {param.default_value}"
        else:
            defval = ""
        prefix = param.prefix or ""

        if param.type is None:
            return f"{prefix}{param.name}{defval}"
        if not param.name:
            return f"{prefix}{self.print_ref(param.type, link=link)}"
        return (f"{prefix}{param.name}: {self.print_ref(param.type, link=link)}{defval}".strip())

    def _method_prefix(self, method: Member, *, link: bool = True) -> str:
        return "fun"

    def _method_suffix(self, method: Member, *, link: bool = True) -> str:
        if method.returns:
            return f": {self.print_ref(method.returns.type, link=link)}"
        return ""
