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
"""Match return values to expected results."""

from abc import ABC, abstractmethod

from asciidoxy.model import Compound, Parameter, ReturnValue, ThrowsClause, TypeRef


class Matcher(ABC):
    def assert_matches(self, other) -> None:
        result = self.matches(other)
        assert len(result) == 0, "\n".join(result)

    def assert_not_matches(self, other) -> None:
        assert len(self.matches(other)) > 0, "Should not match!"

    @abstractmethod
    def matches(self, other, prefix=""):
        ...


class PartialModel(Matcher):
    """Allow comparing models against a limited set of attributes."""
    def __init__(self, model_type, **expected_values):
        self._model_type = model_type
        self._expected_values = expected_values

    def matches(self, other, prefix=""):
        if other is None:
            return ["Not expecting None"]
        if not isinstance(other, self._model_type):
            return [f"Unexpected type: {type(other).__name__} != {self._model_type.__name__}"]

        mismatches = []
        for attr_name, expected_value in self._expected_values.items():
            value = getattr(other, attr_name)
            if isinstance(expected_value, (tuple, list)):
                if not isinstance(value, (tuple, list)):
                    mismatches.append(f"{prefix}{attr_name}: {value} is not a list")
                elif len(value) != len(expected_value):
                    mismatches.append(
                        f"len({prefix}{attr_name}): {len(value)} != {len(expected_value)}")
                else:
                    for i, (sub_value, sub_expected_value) in enumerate(zip(value, expected_value)):
                        mismatches.extend(
                            match_single(f"{prefix}{attr_name}[{i}]", sub_value,
                                         sub_expected_value))
            else:
                mismatches.extend(match_single(f"{prefix}{attr_name}", value, expected_value))
        return mismatches

    def __repr__(self) -> str:
        expected = "\n".join(f"{key} [{value}]" for key, value in self._expected_values.items())
        return f"{self._model_type.__name__}:\n{expected}"


def match_single(name, value, expected_value):
    if isinstance(expected_value, Matcher):
        return expected_value.matches(value, f"{name}.")
    elif value != expected_value:
        return [f"{name}: {value} != {expected_value}"]
    return []


class Unordered(Matcher):
    def __init__(self, *values):
        self.values = values

    def matches(self, other, prefix=""):
        if not isinstance(other, (tuple, list)):
            return [f"{prefix}: {other} is not a list"]
        else:
            not_found_yet = list(self.values)
            too_much = []
            for value in other:
                for expected in not_found_yet:
                    if len(match_single("", value, expected)) == 0:
                        not_found_yet.remove(expected)
                        break
                else:
                    too_much.append(value)

            return ([f"{prefix}[*]: missing {value}" for value in not_found_yet] +
                    [f"{prefix}[*]: unexpected {value}" for value in too_much])


class AtLeast(Matcher):
    def __init__(self, *values):
        self.values = values

    def matches(self, other, prefix=""):
        if not isinstance(other, (tuple, list)):
            return [f"{prefix}: {other} is not a list"]
        else:
            not_found_yet = list(self.values)
            for value in other:
                for expected in not_found_yet:
                    if len(match_single("", value, expected)) == 0:
                        not_found_yet.remove(expected)
                        break

            return [f"{prefix}[*]: missing {value}" for value in not_found_yet]


class HasNot(Matcher):
    def __init__(self, *values):
        self.values = values

    def matches(self, other, prefix=""):
        if not isinstance(other, (tuple, list)):
            return [f"{prefix}: {other} is not a list"]
        else:
            for value in other:
                for expected in self.values:
                    if len(match_single("", value, expected)) == 0:
                        return [f"{prefix}[*]: should not contain {value}"]
        return []


class IsEmpty(Matcher):
    def matches(self, other, prefix=""):
        if isinstance(other, (tuple, list)):
            if len(other) > 0:
                return [f"{prefix}[]: is not empty"]
        else:
            if other:
                return [f"{prefix}: {other} is not empty"]
        return []


class IsNotEmpty(Matcher):
    def matches(self, other, prefix=""):
        if isinstance(other, (tuple, list)):
            if len(other) == 0:
                return [f"{prefix}[]: is empty"]
        else:
            if not other:
                return [f"{prefix}: {other} is empty"]
        return []


class IsFalse(Matcher):
    def matches(self, other, prefix=""):
        if other is not False:
            return [f"{prefix}: is not False"]
        return []


class IsTrue(Matcher):
    def matches(self, other, prefix=""):
        if other is not True:
            return [f"{prefix}: is not True"]
        return []


class IsNone(Matcher):
    def matches(self, other, prefix=""):
        if other is not None:
            return [f"{prefix}: is not None"]
        return []


class SizeIs(Matcher):
    def __init__(self, length):
        self.length = length

    def matches(self, other, prefix=""):
        if other is None:
            return [f"{prefix}: should be empty sequence"]
        if len(other) != self.length:
            return [f"len({prefix}): {len(other)} != {self.length}"]
        return []


def m_compound(**kwargs):
    return PartialModel(Compound, **kwargs)


def m_parameter(**kwargs):
    return PartialModel(Parameter, **kwargs)


def m_returnvalue(**kwargs):
    return PartialModel(ReturnValue, **kwargs)


def m_typeref(**kwargs):
    return PartialModel(TypeRef, **kwargs)


def m_throwsclause(**kwargs):
    return PartialModel(ThrowsClause, **kwargs)
