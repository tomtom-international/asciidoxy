/*
 * Copyright (C) 2019, TomTom (http://tomtom.com).
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
package asciidoxy

/**
 * Class to hold information about a coordinate.
 *
 * A coordinate has a latitude, longitude, and an altitude.
 *
 * @property latitude The latitude in degrees.
 * @property longitude The longitude in degrees.
 * @property altitude The altitude in meters.
 */
class Coordinate(
    val latitude: Double,
    val longitude: Double,
    val altitude: Double) {

    /**
     * Check if the coordinate is valid.
     *
     * A coordinate is valid if its values are within WGS84 bounds.
     *
     * @return True if valid, false if not.
     */
    fun isValid(): Boolean { ... }

    companion object {
        /**
         * Create a coordinate without altitude.
         *
         * @param latitude The latitude in degrees.
         * @param longitude The longitude in degrees.
         */
        fun create(latitude: Double, longitude: Double): Coordinate { ... }

        /**
         * Invalid value for latitudes and longitudes.
         */
        const val INVALID: Double = -181.0
    }
}
