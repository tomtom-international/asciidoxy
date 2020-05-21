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

#include <same_in_multiple_namespaces.hpp>

namespace asciidoxy {

/**
 * Create a convertor from namespace asciidoxy.
 */
Convertor CreateConvertor();

namespace geometry {

/**
 * Create a convertor from namespace asciidoxy::geometry.
 */
Convertor CreateConvertor();

}  // namespace geometry

namespace traffic {

/**
 * Create a convertor from namespace asciidoxy::traffic.
 */
Convertor CreateConvertor();

namespace geometry {

/**
 * Create a convertor in a namespace without its own convertor. Ambiguous reference to return type.
 */
Convertor CreateConvertor();

}  // namespace geometry
}  // namespace traffic
}  // namespace asciidoxy

