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
"""Filters for selecting which parts of elements are generated."""

import re

from abc import ABC, abstractmethod
from enum import Enum
from typing import Pattern, Sequence


class FilterAction(Enum):
    """Action to take based on the filter."""
    INCLUDE = 1
    """Include the item."""

    EXCLUDE = 2
    """Exclude the item."""

    NEUTRAL = 3
    """Do not change whether the item is included or excluded."""


class StringFilter(ABC):
    """Filter string values."""
    @abstractmethod
    def __call__(self, value: str) -> FilterAction:
        return FilterAction.NEUTRAL


class AllStringFilter(StringFilter):
    """Include all values."""
    def __call__(self, value: str) -> FilterAction:
        return FilterAction.INCLUDE


class NoneStringFilter(StringFilter):
    """Exclude all values."""
    def __call__(self, value: str) -> FilterAction:
        return FilterAction.EXCLUDE


class IncludeStringFilter(StringFilter):
    """Include values that match a regular expression."""
    include_pattern: Pattern

    def __init__(self, include_pattern: str):
        self.include_pattern = re.compile(include_pattern)

    def __call__(self, value: str) -> FilterAction:
        if self.include_pattern.match(value) is not None:
            return FilterAction.INCLUDE
        else:
            return FilterAction.NEUTRAL


class ExcludeStringFilter(StringFilter):
    """Exclude all values that match a regular expression."""
    exclude_pattern: Pattern

    def __init__(self, exclude_pattern: str):
        self.exclude_pattern = re.compile(exclude_pattern)

    def __call__(self, value: str) -> FilterAction:
        if self.exclude_pattern.match(value) is not None:
            return FilterAction.EXCLUDE
        else:
            return FilterAction.NEUTRAL


class ChainedStringFilter(StringFilter):
    """Ordered chain of string filters.

    The last non-neutral filter action determines the outcome of this filter.
    """
    filters: Sequence[StringFilter]

    def __init__(self, *filters: StringFilter):
        self.filters = filters

    def __call__(self, value: str) -> FilterAction:
        combined_action = FilterAction.NEUTRAL
        for f in self.filters:
            action = f(value)
            if action is not FilterAction.NEUTRAL:
                combined_action = action
        return combined_action
