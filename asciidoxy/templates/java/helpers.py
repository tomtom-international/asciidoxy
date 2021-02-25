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
"""Helper functions for Java templates."""

from typing import Iterator

from asciidoxy.model import Compound
from asciidoxy.templates.helpers import TemplateHelper


class JavaTemplateHelper(TemplateHelper):
    def constants(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if (m.kind == "variable" and m.prot == prot and m.returns and m.returns.type
                    and m.returns.type.prefix and "final" in m.returns.type.prefix))
