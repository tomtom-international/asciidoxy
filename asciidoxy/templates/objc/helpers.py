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
"""Helper functions for Objective C templates."""

from asciidoxy.model import Compound
from asciidoxy.templates.helpers import TemplateHelper


class ObjcTemplateHelper(TemplateHelper):
    def method_signature(self, method: Compound, max_width: int = 80) -> str:
        assert method.returns is not None

        method_name_parts = method.name.split(":")
        static = "+" if method.static else "-"

        if len(method_name_parts) == 1:
            return f"{static} ({self.print_ref(method.returns.type)}){method.name}"

        method_parts = []
        for method_name_part, param in zip(method_name_parts, method.params):
            method_parts.append(f"{method_name_part}:({self.print_ref(param.type)}){param.name}")

        prefix = f"{static} ({self.print_ref(method.returns.type)})"

        if len(method_parts) > 1:
            first_line_text = (f"- ({self.print_ref(method.returns.type, link=False)})"
                               f"{method_parts[0]}")
            first_line_colon_position = first_line_text.find(":")
            assert first_line_colon_position > 0

            formatted = [f"{prefix}{method_parts[0]}"]
            for line in method_parts[1:]:
                colon_position = line.find(":")
                if colon_position < first_line_colon_position:
                    line = " " * (first_line_colon_position - colon_position) + line
                formatted.append(line)
            method_parts = formatted

            return "\n".join(method_parts)
        else:
            return f"{prefix}{method_parts[0]}"

    def block_definition(self, block: Compound) -> str:
        assert block.returns is not None
        assert block.returns.type is not None
        assert block.returns.type.args is not None

        if block.name:
            block_name = f" {block.name}"
        else:
            block_name = ""

        return (f"typedef {self.print_ref(block.returns.type, skip_args=True)}(^{block_name})"
                f" {self.argument_list(block.returns.type.args)}")

    class_methods = TemplateHelper.static_methods
