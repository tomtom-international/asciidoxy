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

#import <exception>
#import <tuple>

namespace asciidoxy {
namespace geometry {

class InvalidCoordinate : public std::exception {
 public:
  const char* what() const noexcept;
};

/**
 * Class to hold information about a coordinate.
 *
 * A coordinate has a latitude, longitude, and an altitude.
 */
class Coordinate {
 public:
  /**
   * Default constructor.
   */
  Coordinate();

  /**
   * Destructor.
   */
  ~Coordinate();

  /**
   * Coordinates can be added.
   */
  Coordinate operator+(const Coordinate& other) const;

  /**
   * Latitude.
   *
   * @returns The latitude in degrees.
   */
  double Latitude() const;

  /**
   * Longitude.
   *
   * @returns The longitude in degrees.
   */
  double Longitude() const;

  /**
   * Altitude.
   *
   * @returns The altitude in meters.
   */
  double Altitude() const;

  /**
   * Check if the coordinate is valid.
   *
   * A coordinate is valid if its values are within WGS84 bounds.
   *
   * @returns True if valid, false if not.
   */
  bool IsValid() const;

  /**
   * Update from another coordinate.
   */
  void Update(const Coordinate& coordinate);

  /**
   * Update from a tuple of latitude, longitude and altitue.
   */
  void Update(std::tuple<double, double, double> coordinate);

  /**
   * Update from a tuple of only latitude and longitude.
   */
  void Update(std::tuple<double, double> coordinate);

  /**
   * Update latitude and longitude.
   *
   * Altitude remains unchanged.
   */
  void Update(double latitude, double longitude);

  /**
   * Update from separate values.
   */
  void Update(double latitude, double longitude, double altitude);

 private:
  double latitude_{0.0};
  double longitude_{0.0};
  double altitude_{0.0};
};

}  // namespace geometry
}  // namespace asciidoxy
