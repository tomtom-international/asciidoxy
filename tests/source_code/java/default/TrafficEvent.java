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
package com.asciidoxy.traffic;

/**
 * Information about a traffic event.
 */
public class TrafficEvent {
   /**
    * Severity scale for traffic events.
    *
    * The more severe the traffic event, the more likely it is to have a large delay.
    */
   public enum Severity {
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
  public class TrafficEventData {
    /**
     * TPEG cause code.
     */
    public int cause;

    /**
     * Delay caused by the traffic event in seconds.
     */
    public int delay;

    /**
     * Severity of the event.
     */
    public Severity severity;
  };

  /**
   * Construct a traffic event from data.
   *
   * @param data The data to contain.
   */
  public TrafficEvent(TrafficEventData data) {}

  /**
   * Get the traffic event details.
   *
   * @return Traffic event details.
   */
  public TrafficEventData Data() { return data_; }

  /**
   * Update the traffic event data.
   *
   * Verifies the new information before updating.
   *
   * @param cause New TPEG cause code.
   * @param delay New delay in seconds.
   * @returns True if the update is valid.
   */
  public boolean Update(int cause, int delay) { return false; }

  private TrafficEventData data_;
};
