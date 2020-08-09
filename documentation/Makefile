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

export DOC_BUILD_DIR = $(BUILD_DIR)/doc

docs: $(DOC_BUILD_DIR)/output/index.html

$(DOC_BUILD_DIR):
	mkdir -p $(DOC_BUILD_DIR)

$(DOC_BUILD_DIR)/doxygen: $(DOC_BUILD_DIR)
	mkdir -p $(DOC_BUILD_DIR)/doxygen

$(DOC_BUILD_DIR)/asciidoxy: $(DOC_BUILD_DIR)
	mkdir -p $(DOC_BUILD_DIR)/asciidoxy

$(DOC_BUILD_DIR)/doxygen/xml: $(DOC_BUILD_DIR)/doxygen
	doxygen

$(CURDIR)/copy: $(ROOT_DIR)/CHANGELOG.adoc
	mkdir -p copy
	cp $(ROOT_DIR)/CHANGELOG.adoc copy/

$(CURDIR)/source_code:
	cp -r $(ROOT_DIR)/tests/source_code source_code

ADOC_IN_FILES := $(wildcard *.adoc)
ADOC_OUT_FILES := $(patsubst %.adoc,%.html,$(addprefix $(DOC_BUILD_DIR)/output/, $(ADOC_IN_FILES)))

$(ADOC_OUT_FILES): $(ADOC_IN_FILES) $(DOC_BUILD_DIR)/asciidoxy $(CURDIR)/asciidoxy.toml $(CURDIR)/copy $(CURDIR)/source_code $(DOC_BUILD_DIR)/doxygen/xml
	asciidoxy index.adoc \
		--build-dir $(DOC_BUILD_DIR)/asciidoxy \
		--destination-dir $(DOC_BUILD_DIR)/output \
		--spec-file asciidoxy.toml \
		--debug --multipage \
		-a linkcss

#examples/cpp:
#	cd examples/cpp && $(MAKE)
