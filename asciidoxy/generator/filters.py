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
"""Filters for selecting which parts of elements are generated."""

import collections
import re
import sys

from abc import ABC, abstractmethod
from enum import Enum
from typing import Generator, List, Mapping, Optional, Pattern, Sequence, Type, TypeVar, Union

from ..model import Compound, ThrowsClause


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

    if sys.version_info < (3, 7):

        def __deepcopy__(self, memo):
            return IncludeStringFilter(self.include_pattern.pattern)


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

    if sys.version_info < (3, 7):

        def __deepcopy__(self, memo):
            return ExcludeStringFilter(self.exclude_pattern.pattern)


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


FilterSpec = Union[str, Sequence[str], Mapping[str, Union[str, Sequence[str]]]]
"""Complex type hint for element filter specifications."""

FilterType = TypeVar("FilterType", bound="ElementFilter")
"""Type hint for ElementFilter factory methods."""


class ElementFilter(ABC):
    """Base class for element filters."""
    @abstractmethod
    def __init__(self, **kwargs):
        pass

    @classmethod
    def from_spec(cls: Type[FilterType], spec: Optional[FilterSpec]) -> Optional[FilterType]:
        """Construct the filter from a filter specification."""
        if spec is None:
            return None

        if isinstance(spec, collections.abc.Mapping):
            kwargs = {f"{a}_filter": filter_from_strings(s) for a, s in spec.items()}
        else:
            kwargs = {"name_filter": filter_from_strings(spec)}

        return cls(**kwargs)


class MemberFilter(ElementFilter):
    """Filter for selecting members (of a compound) to insert.

    Attributes:
        name_filter: Filter for the name of the members to include.
        kind_filter: Filter for the kind of the members to include.
        prot_filter: Filter for the protection level of the members to include.
    """
    name_filter: StringFilter
    kind_filter: StringFilter
    prot_filter: StringFilter

    # TODO static_filter: BoolFilter

    def __init__(self,
                 name_filter: Optional[StringFilter] = None,
                 kind_filter: Optional[StringFilter] = None,
                 prot_filter: Optional[StringFilter] = None):
        self.name_filter = name_filter or AllStringFilter()
        self.kind_filter = kind_filter or AllStringFilter()
        self.prot_filter = prot_filter or AllStringFilter()

    def __call__(self, member: Compound) -> bool:
        """Apply the filter to a member.

        Returns:
            True if the member should be included.
        """
        if self.name_filter(member.name) is FilterAction.EXCLUDE:
            return False
        if self.kind_filter(member.kind) is FilterAction.EXCLUDE:
            return False
        if self.prot_filter(member.prot) is FilterAction.EXCLUDE:
            return False
        return True


class ExceptionFilter(ElementFilter):
    """Filter for selecting exceptions (of a member) to insert.

    Attributes:
        name_filter: Filter for the name of the exceptions to include.
    """
    name_filter: StringFilter

    def __init__(self, name_filter: StringFilter):
        self.name_filter = name_filter

    def __call__(self, throws_clause: ThrowsClause) -> bool:
        """Apply the filter to an exception in a throws clause.

        Returns:
            True if the exception value should be included.
        """
        if self.name_filter(throws_clause.type.name) is FilterAction.EXCLUDE:
            return False
        return True


def filter_from_strings(filter_strings: Union[str, Sequence[str]]) -> StringFilter:
    """Create a string filter from a sequence of input strings.

    Each string in the sequence can have the following format:
    - `ALL`: Accept all strings.
    - `NONE`: Accept no strings.
    - `<regex>` or `+<regex>`: Include strings matching the regex.
    - `-<regex>`: Exclude strings matching the regex.

    If the first string is an include regex, an implicit NONE is inserted before. If the first
    string is an exclude regex, an implicit ALL is inserted before.

    Args:
        filter_strings: List of filter strings to build the filter from.

    Returns:
        A string filter matching the input specification.
    """
    if isinstance(filter_strings, str):
        filter_strings = [filter_strings]

    filters: List[StringFilter] = []

    for filter_string in filter_strings:
        if filter_string == "ALL":
            filters.append(AllStringFilter())
        elif filter_string == "NONE":
            filters.append(NoneStringFilter())
        elif filter_string.startswith("-"):
            filters.append(ExcludeStringFilter(filter_string[1:]))
        elif filter_string.startswith("+"):
            filters.append(IncludeStringFilter(filter_string[1:]))
        else:
            filters.append(IncludeStringFilter(filter_string))

    if len(filters) > 0:
        if isinstance(filters[0], ExcludeStringFilter):
            filters.insert(0, AllStringFilter())
        elif isinstance(filters[0], IncludeStringFilter):
            filters.insert(0, NoneStringFilter())

    if len(filters) == 0:
        return AllStringFilter()
    elif len(filters) == 1:
        return filters[0]
    else:
        return ChainedStringFilter(*filters)


def combine_strings(first: Union[str, Sequence[str]],
                    second: Union[str, Sequence[str]]) -> Union[str, Sequence[str]]:
    if isinstance(first, str):
        first = [first]
    if isinstance(second, str):
        second = [second]

    return list(first) + list(second)


def combine_specs(first: Optional[FilterSpec],
                  second: Optional[FilterSpec]) -> Optional[FilterSpec]:
    """Combine two filter specs."""
    if first is None and second is None:
        return None
    if first is None:
        return second
    if second is None:
        return first

    if isinstance(first, collections.abc.Mapping) or isinstance(second, collections.abc.Mapping):
        if isinstance(first, (str, collections.abc.Sequence)):
            first = {"name": first}
        if isinstance(second, (str, collections.abc.Sequence)):
            second = {"name": second}

        result = {}
        for key in set(first.keys()) | set(second.keys()):
            if key not in first:
                result[key] = second[key]
            elif key not in second:
                result[key] = first[key]
            else:
                result[key] = combine_strings(first[key], second[key])

        return result

    else:
        return combine_strings(first, second)


class InsertionFilter:
    """Filter members of an element to be inserted."""
    _member_filter: Optional[MemberFilter]
    _exception_filter: Optional[ExceptionFilter]

    _member_spec: Optional[FilterSpec]
    _exception_spec: Optional[FilterSpec]

    def __init__(self,
                 members: Optional[FilterSpec] = None,
                 exceptions: Optional[FilterSpec] = None):
        self._member_spec = members
        self._exception_spec = exceptions

        self._member_filter = MemberFilter.from_spec(members)
        self._exception_filter = ExceptionFilter.from_spec(exceptions)

    def members(self, compound: Compound) -> Generator[Compound, None, None]:
        """Get members matching the filter."""
        for member in compound.members:
            if self._member_filter is None or self._member_filter(member):
                yield member

    def exceptions(self, member: Compound) -> Generator[ThrowsClause, None, None]:
        """Get exceptions matching the filter."""
        for exception in member.exceptions:
            if self._exception_filter is None or self._exception_filter(exception):
                yield exception

    def extend(self,
               members: Optional[FilterSpec] = None,
               exceptions: Optional[FilterSpec] = None) -> "InsertionFilter":
        return InsertionFilter(combine_specs(self._member_spec, members),
                               combine_specs(self._exception_spec, exceptions))
