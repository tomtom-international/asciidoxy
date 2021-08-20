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

#include <memory>

namespace asciidoxy {
namespace traffic {

using TpegCauseCode = int;
typedef int Delay;

/**
 * Information about a traffic event.
 */
class TrafficEvent {
 public:
   /**
    * Severity scale for traffic events.
    *
    * The more severe the traffic event, the more likely it is to have a large delay.
    */
   enum class Severity {
     /**
      * Low severity.
      */
     Low = 1,

     /**
      * Medium severity.
      */
     Medium = 2,

     /**
      * High severity.
      *
      * Better stay away here.
      */
     High = 3,

     /**
      * Severity unknown.
      */
     Unknown = 4
   };

  /**
   * Details about a traffic event.
   *
   * Use the cause and delay to properly inform your users.
   */
  struct TrafficEventData {
    /**
     * TPEG cause code.
     */
    TpegCauseCode cause;

    /**
     * Delay caused by the traffic event in seconds.
     */
    Delay delay;

    /**
     * Severity of the event.
     */
    Severity severity;
  };

  /**
   * Default constructor.
   */
  TrafficEvent();

  /**
   * Construct a traffic event from data.
   *
   * @param data The data to contain.
   */
  TrafficEvent(TrafficEventData data);

  /**
   * Get the traffic event details.
   *
   * @return Traffic event details.
   */
  const TrafficEventData& Data() const;

  /**
   * Update the traffic event data.
   *
   * Verifies the new information before updating.
   *
   * @param cause New TPEG cause code.
   * @param delay New delay in seconds.
   * @returns True if the update is valid.
   */
  bool Update(int cause, int delay);

  /**
   * Get a shared pointer to a copy of the data.
   *
   * Not sure why you want this.
   *
   * @returns The shared pointer.
   * @throws std::runtime_exception Thrown if no copy of the data is available.
   * @throws InvalidEventError Thrown when the event data is invalid.
   */
  std::shared_ptr<TrafficEventData> SharedData() const;

  /**
   * Calculate the current delay.
   *
   * @returns The delay in seconds.
   * @throws std::runtime_exception Thrown when the update encounters a critical error.
   */
  long CalculateDelay();

  /**
   * Register a callback to receive updates for the traffic event.
   *
   * @param callback A function to call on updates.
   */
  void RegisterTrafficCallback(std::function<void(const TrafficEventData&, int delay)> callback);

 private:
  TrafficEventData data_;
};

}  // namespace traffic
}  // namespace asciidoxy
