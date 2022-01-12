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
"""Fixtures for type parser tests."""

from unittest.mock import MagicMock

import pytest


class DriverMock(MagicMock):
    def assert_unresolved(self, *names):
        assert (sorted([args[0].name
                        for args, _ in self.unresolved_ref.call_args_list]) == sorted(names))


@pytest.fixture
def driver_mock():
    return DriverMock()
