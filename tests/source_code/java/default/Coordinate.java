/*
 * Copyright (C) 2019-2020, TomTom (http://tomtom.com).
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
package com.asciidoxy.geometry;

/**
 * Class to hold information about a coordinate.
 *
 * A coordinate has a latitude, longitude, and an altitude.
 */
public class Coordinate {
  /**
   * Default constructor.
   */
  public Coordinate() {}

  /**
   * Latitude.
   *
   * @return The latitude in degrees.
   */
  public double Latitude() { return 0.0; }

  /**
   * Longitude.
   *
   * @return The longitude in degrees.
   */
  public double Longitude() { return 0.0; }

  /**
   * Altitude.
   *
   * @return The altitude in meters.
   */
  public double Altitude() { return 0.0; }

  /**
   * Check if the coordinate is valid.
   *
   * A coordinate is valid if its values are within WGS84 bounds.
   *
   * @return True if valid, false if not.
   */
  public boolean IsValid() { return true; }

  private double latitude_ = 0.0;
  private double longitude_ = 0.0;
  private double altitude_ = 0.0;
};
