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


class Point:
    """Class representing a simple point."""
    def __init__(self, x: int = 0, y: int = 1):
        """Construct a point.

        Args:
            x: The X coordinate.
            y: The Y coordinate.
        """
        ...

    def increment(self, x: int = 2, y: int = 3) -> "Point":
        """Create a new incremented point.

        Args:
            x: Value to increment the X coordinate with.
            y: Value to increment the Y coordinate with.

        Returns:
            A new incremented Point.
        """
        ...
