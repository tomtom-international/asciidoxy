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
"""Helper functions for Swift templates."""

from typing import Iterator

from asciidoxy.model import Compound
from asciidoxy.templates.helpers import TemplateHelper


class SwiftTemplateHelper(TemplateHelper):
    ARGS_BEFORE_TYPE = True
    ARGS_TO_TYPE = " -> "
    PARAM_NAME_FIRST = True
    PARAM_NAME_SEP = ": "

    def _method_prefix(self, method: Compound, *, link: bool = True) -> str:
        return "func"

    def _method_suffix(self, method: Compound, *, link: bool = True) -> str:
        suffixes = []
        if method.exceptions:
            suffixes.append(" throws")
        if method.returns:
            suffixes.append(f" -> {self.print_ref(method.returns.type, link=link)}")
        return "".join(suffixes)

    def closure_definition(self, closure: Compound) -> str:
        assert closure.returns is not None
        assert closure.returns.type is not None
        assert closure.returns.type.args is not None

        return (f"typealias {closure.name} = {self.argument_list(closure.returns.type.args)}"
                f" -> {self.print_ref(closure.returns.type, skip_args=True)}")

    def static_methods(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if (m.kind == "function" and m.prot == prot and m.static))

    def methods(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if (m.kind == "function" and m.prot == prot and not m.static and m.name != "init"))

    type_methods = static_methods

    def constructors(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.kind == "function" and m.name == "init" and m.prot == prot)
