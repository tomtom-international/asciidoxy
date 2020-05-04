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
"""Modules for generating AsciiDoc output as part of the preprocessing."""

from .asciidoc import process_adoc, Context
from .errors import AsciiDocError
from .filters import InsertionFilter

__all__ = ["process_adoc", "AsciiDocError", "Context", "InsertionFilter"]
