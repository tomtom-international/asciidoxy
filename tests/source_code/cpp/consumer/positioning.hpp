/*
 * Copyright (C) 2019-2021, TomTom (http://tomtom.com).
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <coordinate.hpp>
#include <traffic_event.hpp>

namespace asciidoxy {
namespace positioning {

/**
 * Positioning engine.
 */
class Positioning {
 public:
  /**
   * Retrieve the current position.
   *
   * @returns Coordinates of the current position.
   */
  asciidoxy::geometry::Coordinate CurrentPosition() const;

  /**
   * Check if the given coordinates are nearby.
   *
   * @param coord Coordinates to check.
   * @returns True if the coordinates are nearby.
   */
  bool IsNearby(asciidoxy::geometry::Coordinate coord) const;

  /**
   * Override the current position.
   *
   * @param coord Coordinate to use for the current position.
   * @throws asciidoxy::geometry::InvalidCoordinate Thrown if the given coordinates are not valid.
   */
  void Override(asciidoxy::geometry::Coordinate coord);

  /**
   * Get nearby traffic.
   *
   * @throws geometry::InvalidCoordinate Thrown if the current position is not valid.
   */
  std::vector<traffic::TrafficEvent> TrafficNearby() const;

  /**
   * Are we currently in the given traffic event?
   *
   * @param event The traffic event to check.
   * @returns True if we are in the traffic event.
   */
  bool InTraffic(const traffic::TrafficEvent& event) const;
};

/*
 * Type used for traffic.
 */
using Traffic = asciidoxy::traffic::TrafficEvent;

}  // namespace positioning
}  // namespace asciidoxy
