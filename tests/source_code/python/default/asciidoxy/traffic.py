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

from enum import Enum


class TrafficEvent:
    """Information about a traffic event."""
    _data: "TrafficEvent.TrafficEventData"

    class Severity(Enum):
        """Severity scale for traffic events.

        The more severe the traffic event, the more likely it is to have a large delay.
        """
        Low = 1
        """Low severity."""
        Medium = 2
        """Medium severity."""
        High = 3
        """High severity.

        Better stay away here.
        """
        Unknown = 4
        """Severity unknown."""

    class TrafficEventData:
        """Details about a traffic event.

        Use the cause and delay to properly inform you users.

        Attributes:
            cause:    TPEG cause code.
            delay:    Delay caused by the traffic event in seconds.
            severity: Severity of the event.
        """
        cause: int
        delay: int
        severity: "TrafficEvent.Severity"

        def __init__(self):
            self.cause = 0
            self.delay = 0
            self.severity = self.Severity.Unknown

    def __init__(self, data: "TrafficEvent.TrafficEventData"):
        self._data = data

    def update(self, cause: int, delay: int) -> bool:
        """Update the traffic event data.

        Verifies the new information before updating.

        Args:
            cause: New TPEG cause code.
            delay: New delay in seconds.

        Returns:
            True if the update is valid.
        """
        ...

    def calculate_delay(self) -> int:
        """Calculate the current delay.

        Returns:
            The delay in seconds.

        Raises:
            RuntimeError: Thrown when the update encounters a critical error.
        """
        ...

    def refresh_data(self) -> None:
        """Refresh the traffic event data.

        Raises:
            NoDataError:      Thrown when there is no data to refresh.
            InvalidDataError: Thrown when the data is invalid.
        """
        ...
