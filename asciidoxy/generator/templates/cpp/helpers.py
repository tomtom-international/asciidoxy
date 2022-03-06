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
"""Helper functions for C++ templates."""

from typing import Iterator

from asciidoxy.generator.templates.helpers import (
    TemplateHelper,
    has,
    modifiers,
    param_filter,
    spaced_join,
)
from asciidoxy.model import Compound


class CppTemplateHelper(TemplateHelper):
    def constructors(self, prot: str) -> Iterator[Compound]:
        return (m for m in super().constructors(prot) if not has(modifiers(m, "default", "delete")))

    def destructors(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        destructor_name = f"~{self.element.name}"
        return (m for m in self.insert_filter.members(self.element)
                if (m.kind == "function" and m.name == destructor_name and m.prot == prot
                    and not has(modifiers(m, "default", "delete"))))

    def static_methods(self, prot: str) -> Iterator[Compound]:
        return (m for m in super().static_methods(prot) if not m.name.startswith("operator"))

    def methods(self, prot: str) -> Iterator[Compound]:
        return (m for m in super().methods(prot) if (
            not m.name.startswith("operator") and not has(modifiers(m, "default", "delete"))))

    def operators(self, prot: str) -> Iterator[Compound]:
        return (m for m in super().methods(prot)
                if (m.name.startswith("operator") and not has(modifiers(m, "default", "delete"))))

    def _method_prefix(self, method: Compound, *, link: bool = True) -> str:
        if has(param_filter(method.params, kind="tparam")):
            template = self.type_list(method.params,
                                      link=link,
                                      kind="tparam",
                                      start="template<",
                                      end=">\n")
        else:
            template = ""
        return spaced_join(template, *modifiers(method, "constexpr"),
                           super()._method_prefix(method, link=link))
