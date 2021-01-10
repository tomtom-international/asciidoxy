# Copyright (C) 2019-2020, TomTom (http://tomtom.com).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

.PHONY: generate-test-source-kitten

JSON_DIR := ../../../generated/source_kitten/swift/default

$(JSON_DIR):
	mkdir -p $@

define SOURCEKITTEN_template
_SWIFT_FILE := $(1)
_DOC_JSON_FILE := $(addprefix $(JSON_DIR)/,$(addsuffix .doc.json,$(1)))
_STRUCTURE_JSON_FILE := $(addprefix $(JSON_DIR)/,$(addsuffix .structure.json,$(1)))

$$(_DOC_JSON_FILE): $$(_SWIFT_FILE) $(JSON_DIR)
	sourcekitten doc --single-file $$< > $$@

$$(_STRUCTURE_JSON_FILE): $$(_SWIFT_FILE) $(JSON_DIR)
	sourcekitten structure --file $$< > $$@

JSON_FILES := $$(JSON_FILES) $$(_DOC_JSON_FILE) $$(_STRUCTURE_JSON_FILE)
endef

$(foreach swift_file,$(wildcard *.swift),$(eval $(call SOURCEKITTEN_template,$(swift_file))))

generate-test-source-kitten: $(JSON_FILES)
