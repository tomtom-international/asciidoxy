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
"""
Shared functionality for unit tests.
"""

import xml.etree.ElementTree as ET

from typing import Optional


def sub_element(parent, tag, text=None, tail=None, **attribs):
    e = ET.SubElement(parent, tag, **attribs)
    if text is not None:
        e.text = text
    if tail is not None:
        e.tail = tail
    return e


def assert_equal_or_none_if_empty(value: Optional[str], text: str) -> None:
    if not text:
        assert not value
    else:
        assert value == text


class ProgressMock:
    def __init__(self):
        self.total = 0
        self.ready = 0

    def update(self, n=1):
        self.ready += n
