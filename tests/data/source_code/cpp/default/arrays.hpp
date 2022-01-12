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

namespace asciidoxy {
namespace arrays {

/**
 * Some simple struct.
 */
class SomeStruct {
  int value;
};

/**
 * A simple array of simple structs.
 */
using StructArray = SomeStruct[];

/**
 * Another simple array of simple structs.
 */
typedef SomeStruct[] AnotherArray;

/**
 * A function accepting and returning an array.
 *
 * @param input The input array.
 * @returns Another array.
 */
SomeStruct[] process(const SomeStruct[] input);

}  // namespace arrays
}  // namespace asciidoxy
