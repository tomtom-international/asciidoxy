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

#include <functional>
#include <memory>
#include <string>

namespace asciidoxy {

namespace relative_namespace {

namespace detail {

class ErrorDescriptor {
};

class SuccessDescriptor {
};

}  // namespace detail

class InterfaceWithDetailClasses {
 public:
  /**
   * Do something with piece of text.
   *
   * @param text The text to do something with.
   * @param success_callback Invoked when successful.
   * @param error_callback Invoked on error.
   */
  void DoSomething(const std::string& text,
                   std::function<void(const std::shared_ptr<detail::SuccessDescriptor>&)> success_callback,
                   std::function<void(detail::ErrorDescriptor)> error_callback);
};

}  // namespace relative_namespace
}  // namespace asciidoxy
