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
"""Helper functions for python reference templates."""

from typing import Iterator

from asciidoxy.model import Compound, Parameter
from asciidoxy.templates.helpers import TemplateHelper


class PythonTemplateHelper(TemplateHelper):
    NESTED_START: str = "["
    NESTED_END: str = "]"
    PARAM_NAME_FIRST = True
    PARAM_NAME_SEP = ": "

    def parameter(self, param: Parameter, *, link: bool = True, default_value: bool = False) -> str:
        if param.type is not None and param.type.name in ("self", "cls"):
            return param.type.name

        return super().parameter(param, link=link, default_value=default_value)

    def _method_prefix(self, method: Compound, *, link: bool = True) -> str:
        return "def"

    def _method_suffix(self, method: Compound, *, link: bool = True) -> str:
        return f" -> {self.print_ref(method.returns.type, link=link)}" if method.returns else ""

    def static_methods(self, prot: str) -> Iterator[Compound]:
        return (m for m in super().static_methods(prot) if not m.name.startswith("_"))

    def methods(self, prot: str):
        return (m for m in super().methods(prot) if not m.name.startswith("_"))

    def constructors(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.kind == "function" and m.name == "__init__")

    def complex_enclosed_types(self, prot: str) -> Iterator[Compound]:
        return (m for m in super().complex_enclosed_types(prot) if not m.name.startswith("_"))

    def variables(self, prot: str) -> Iterator[Compound]:
        return (m for m in super().variables(prot) if not m.name.startswith("_"))


def params(method: Compound) -> Iterator[Parameter]:
    return (param for param in method.params
            if (not param.type or param.type.name not in ("self", "cls")))
