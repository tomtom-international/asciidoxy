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

from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.templates.helpers import TemplateHelper


class PythonTemplateHelper(TemplateHelper):
    NESTED_START: str = "["
    NESTED_END: str = "]"

    def type_and_name(self, param, *, link: bool = True):
        if param.type is None or not param.type.name:
            return param.name
        if param.type.name in ("self", "cls"):
            return param.type.name
        return (f"{param.name}: {self.print_ref(param.type, link=link)}".strip())

    def _method_prefix(self, method, *, link: bool = True) -> str:
        return "def"

    def _method_suffix(self, method, *, link: bool = True) -> str:
        return f" -> {self.print_ref(method.returns.type, link=link)}" if method.returns else ""


def params(element):
    return (param for param in element.params
            if (not param.type or param.type.name not in ("self", "cls")))


def public_static_methods(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if (m.kind == "function" and m.returns and not m.name.startswith("_") and m.static))


def public_methods(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if (m.kind == "function" and m.returns and not m.name.startswith("_") and not m.static))


def public_constructors(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if m.kind == "function" and m.name == "__init__")


def public_enclosed_types(element, insert_filter: InsertionFilter):
    return (m.referred_object for m in insert_filter.inner_classes(element)
            if m.referred_object is not None and not m.name.startswith("_"))


def public_variables(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if m.kind == "variable" and not m.name.startswith("_"))
