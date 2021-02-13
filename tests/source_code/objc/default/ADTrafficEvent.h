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

#import <Foundation/Foundation.h>

/*!
 Type for TPEG cause codes.
 */
typedef NSInteger TpegCauseCode;

/*!
 Details about a traffic event.

 Use the cause and delay to properly inform your users.
 */
@interface TrafficEventData : NSObject

/*!
 Severity scale for traffic events.

 The more severe the traffic event, the more likely it is to have a large delay.
 */
typedef enum {
 /**
  * Low severity.
  */
 ADSeverityLow = 1,

 /**
  * Medium severity.
  */
 ADSeverityMedium = 2,

 /**
  * High severity.
  *
  * Better stay away here.
  */
 ADSeverityHigh = 3,

 /**
  * Severity unknown.
  */
 ADSeverityUnknown = 4
} ADSeverity;

/*!
 TPEG cause code.
 */
TpegCauseCode cause;

/*!
 Delay caused by the traffic event in seconds.
 */
NSInteger delay;

/*!
 Severity of the event.
 */
Severity severity;
};
@end

/*!
 Information about a traffic event.
 */
@protocol ADTrafficEvent <NSObject>

/*!
 Traffic event details.
 */
@property(nonatomic, readonly) TrafficEventData data;

/*!
 Update the traffic event data.

 Verifies the new information before updating.

 @param cause New TPEG cause code.
 @param delay New delay in seconds.
 @returns True if the update is valid.
 */
- BOOL updateWithCause:(NSInteger)cause
              andDelay:(NSInteger)delay;

@end

/*!
 Callback for receiving new traffic events.
 */
typedef void (^OnTrafficEventCallback)(id<ADTrafficEvent>, NSInteger delay);
