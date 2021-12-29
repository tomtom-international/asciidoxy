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

/**
 * \file
 */

#include <stdint.h>

namespace asciidoxy {
namespace wifi {

constexpr uint8_t WIFI_PROTOCOL_11B = 0x01;
constexpr uint8_t WIFI_PROTOCOL_11N = 0x02;
constexpr uint8_t WIFI_PROTOCOL_11G = 0x04;
constexpr uint8_t WIFI_PROTOCOL_LR = 0x10;

enum class ESP32WiFiProtocol : uint8_t {
    eWIFI_11B = WIFI_PROTOCOL_11B,                                            ///< 802.11b
    eWIFI_11BG = WIFI_PROTOCOL_11B | WIFI_PROTOCOL_11G,                       ///< 802.11bg
    eWIFI_11BGN = WIFI_PROTOCOL_11B | WIFI_PROTOCOL_11G | WIFI_PROTOCOL_11N,  ///< 802.11bgn
    eWIFI_LR = WIFI_PROTOCOL_LR,                                              ///< ESP custom LR protocol
    eWIFI_11BGNLR = WIFI_PROTOCOL_11B | WIFI_PROTOCOL_11G | WIFI_PROTOCOL_11N | WIFI_PROTOCOL_LR,  ///< 802.11bgn+LR
    eERROR                                                                                         ///< error
};

}  // namespace
}  // namespace
