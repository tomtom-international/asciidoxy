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
"""Helper functions for python reference templates."""

from typing import Iterator

from asciidoxy.model import Compound, Member, Parameter
from asciidoxy.templates.helpers import TemplateHelper


class PythonTemplateHelper(TemplateHelper):
    NESTED_START: str = "["
    NESTED_END: str = "]"

    def parameter(self, param: Parameter, *, link: bool = True, default_value: bool = False) -> str:
        if default_value and param.default_value:
            defval = f" = {param.default_value}"
        else:
            defval = ""

        if param.type is None or not param.type.name:
            return f"{param.name}{defval}"
        if param.type.name in ("self", "cls"):
            return param.type.name

        return (f"{param.name}: {self.print_ref(param.type, link=link)}{defval}".strip())

    def _method_prefix(self, method: Member, *, link: bool = True) -> str:
        return "def"

    def _method_suffix(self, method: Member, *, link: bool = True) -> str:
        return f" -> {self.print_ref(method.returns.type, link=link)}" if method.returns else ""

    def public_static_methods(self) -> Iterator[Member]:
        return (m for m in super().public_static_methods() if not m.name.startswith("_"))

    def public_methods(self):
        return (m for m in super().public_methods() if not m.name.startswith("_"))

    def public_constructors(self) -> Iterator[Member]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.kind == "function" and m.name == "__init__")

    def public_complex_enclosed_types(self) -> Iterator[Compound]:
        return (m for m in super().public_complex_enclosed_types() if not m.name.startswith("_"))

    def public_variables(self) -> Iterator[Member]:
        return (m for m in super().public_variables() if not m.name.startswith("_"))


def params(method: Member) -> Iterator[Parameter]:
    return (param for param in method.params
            if (not param.type or param.type.name not in ("self", "cls")))
