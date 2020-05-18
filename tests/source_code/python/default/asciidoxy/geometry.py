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

from typing import Optional


class Coordinate:
    """Class to hold information about a coordinate.

    A coordinate has a latitude, longitude, and an altitude.

    Attributes:
        latitude:  Latitude in degrees.
        longitude: Longitude in degrees.
        altitude:  Altitude in meters.
    """
    latitude: float
    longitude: float
    altitude: float

    def __init__(self):
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0

    def is_valid(self) -> bool:
        """Check if the coordinate is valid.

        A coordinate is valid if its values are within WGS84 bounds.

        Returns:
            True if valid, False if not.
        """
        ...

    @classmethod
    def from_string(cls, value: str) -> "Coordinate":
        """Create a coordinate from its string representation."""
        ...

    @staticmethod
    def combine(left: "Coordinate", right: "Coordinate") -> "Coordinate":
        """Combine two coordinates."""
        ...

    @classmethod
    def from_string_safe(cls, value: Optional[str]) -> Optional["Coordinate"]:
        """Create a coordinate from its string representation.

        Accepts None as input.
        """
        ...
