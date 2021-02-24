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

namespace asciidoxy {
namespace system {

/**
 * Base class for services.
 */
class Service {
 public:

  /**
   * Start the service.
   */
  virtual void Start() = 0;

  /**
   * Stop the service.
   */
  virtual void Stop() = 0;
};

/**
 * \interface Service
 * \brief This is an interface for service classes.
 */

/**
 * Helper to start services.
 */
class ServiceStarter {
  friend class Service;
 private:
  /**
   * Register a service that can be started.
   */
  void Register(const Service& service);
};

/**
 * Create a new service.
 *
 * \param name Name of the service to create.
 * \returns The new service, or an empty pointer if it could not be created.
 */
std::unique_ptr<Service> CreateService(std::string name);

}  // namespace system
}  // namespace asciidoxy
