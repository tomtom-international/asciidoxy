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
"""Helper functions for Swift templates."""

from typing import Iterator

from asciidoxy.model import Member, Parameter
from asciidoxy.templates.helpers import TemplateHelper


class SwiftTemplateHelper(TemplateHelper):
    def type_and_name(self, param: Parameter, *, link: bool = True) -> str:
        if param.type is None or not param.type.name:
            return param.name
        if param.type.name in ("self", "cls"):
            return param.type.name
        return (f"{param.name}: {self.print_ref(param.type, link=link)}".strip())

    def _method_prefix(self, method: Member, *, link: bool = True) -> str:
        return "func"

    def _method_suffix(self, method: Member, *, link: bool = True) -> str:
        return f" -> {self.print_ref(method.returns.type, link=link)}" if method.returns else ""

    def block_definition(self, block: Member) -> str:
        assert block.returns is not None
        assert block.returns.type is not None
        assert block.returns.type.args is not None

        if block.name:
            block_name = f" {block.name}"
        else:
            block_name = ""

        return (f"typedef {self.print_ref(block.returns.type, skip_args=True)}(^{block_name})"
                f" {self.argument_list(block.returns.type.args)}")

    def public_simple_enclosed_types(self) -> Iterator[Member]:
        assert self.element is not None
        assert self.insert_filter is not None

        # For some reason enclosed types are always set to private, so ignore visibility
        return (m for m in self.insert_filter.members(self.element)
                if m.kind in ["enum", "class", "protocol"])

    def public_class_methods(self) -> Iterator[Member]:
        return self.public_static_methods()

    def public_constructors(self) -> Iterator[Member]:
        return (m for m in super().public_methods() if m.name.startswith("init"))

    def public_methods(self) -> Iterator[Member]:
        return (m for m in super().public_methods() if not m.name.startswith("init"))
