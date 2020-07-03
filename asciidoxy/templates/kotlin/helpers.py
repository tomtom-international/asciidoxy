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

    def name_colon_type(self, param: Parameter, *, link: bool = True) -> str:
        return f"{param.name}: {self.print_ref(param.type, link=link)}".strip()

    def type_and_name(self, param: Parameter, *, link: bool = True) -> str:
        return self.name_colon_type(param, link=link)

    def method_signature(self, method: Member, max_width: int = 80) -> str:
        method_without_params = self._method_join("fun", method.name)

        if method.returns and method.returns.type.name != "void":
            suffix = ": " + self.print_ref(method.returns.type, link=True)
        else:
            suffix = ""

        if not method.params:
            return (f"{method_without_params}(){suffix}")

        suffix_length = len(self._method_suffix(method, link=False))

        param_sizes = [len(self.name_colon_type(p, link=False)) for p in method.params]
        indent_size = len(method_without_params) + 1
        first_indent = ""

        if any(indent_size + size + 1 + suffix_length > max_width for size in param_sizes):
            indent_size = 4
            first_indent = "\n    "

        param_separator = f",\n{' ' * indent_size}"
        formatted_params = f"{param_separator.join(self.type_and_name(p) for p in method.params)}"

        return (f"{method_without_params}({first_indent}{formatted_params}){suffix}")
