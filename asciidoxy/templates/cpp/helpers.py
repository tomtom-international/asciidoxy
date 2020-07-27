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
"""Helper functions for C++ templates."""

from typing import Iterator

from asciidoxy.model import Member
from asciidoxy.templates.helpers import TemplateHelper


class CppTemplateHelper(TemplateHelper):
    def public_static_methods(self) -> Iterator[Member]:
        return (m for m in super().public_static_methods() if not m.name.startswith("operator"))

    def public_methods(self) -> Iterator[Member]:
        return (m for m in super().public_methods() if not m.name.startswith("operator"))
