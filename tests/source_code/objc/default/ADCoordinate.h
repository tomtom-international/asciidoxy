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

#import <CoreLocation/CLLocation.h>
#import <Foundation/Foundation.h>

/*!
 Class to hold information about a coordinate.

 A coordinate has a latitude, longitude, and an altitude.
 */
@interface ADCoordinate : NSObject

/*!
 The latitude in degrees.
 */
@property(nonatomic, readonly) CLLocationDegrees latitude;

/*!
 The longitude in degrees.
 */
@property(nonatomic, readonly) CLLocationDegrees longitude;

/*!
 The altitude in meters.
 */
@property(nonatomic, readonly) CLLocationDistance altitude;

/*!
 Check if the coordinate is valid.

 A coordinate is valid if its values are within WGS84 bounds.

 @returns True if valid, false if not.
 */
- BOOL isValid;

/*!
 Default constructor.
 */
- (instancetype)init;

@end
