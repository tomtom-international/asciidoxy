# Copyright (C) 2019-2021, TomTom (http://tomtom.com).
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

.PHONY: docs
.SUFFIXES:

export DOC_BUILD_DIR := $(BUILD_DIR)/doc
export DOXYGEN_BUILD_DIR := $(DOC_BUILD_DIR)/doxygen
MULTIPAGE ?= --multipage

docs: $(DOC_BUILD_DIR)/output/index.html

$(DOC_BUILD_DIR):
	mkdir -p $(DOC_BUILD_DIR)

$(DOXYGEN_BUILD_DIR): $(DOC_BUILD_DIR)
	mkdir -p $(DOXYGEN_BUILD_DIR)

$(DOC_BUILD_DIR)/asciidoxy: $(DOC_BUILD_DIR)
	mkdir -p $(DOC_BUILD_DIR)/asciidoxy

$(DOXYGEN_BUILD_DIR)/asciidoxy: $(DOXYGEN_BUILD_DIR)
	mkdir -p $(DOXYGEN_BUILD_DIR)/asciidoxy

$(DOXYGEN_BUILD_DIR)/asciidoxy/xml: $(DOXYGEN_BUILD_DIR)/asciidoxy
	. $(BUILD_DIR)/doxygen-$(LATEST_DOXYGEN_VERSION)/activate_run.sh; doxygen

$(CURDIR)/copy: $(ROOT_DIR)/CHANGELOG.adoc
	mkdir -p copy
	cp $(ROOT_DIR)/CHANGELOG.adoc copy/

EXAMPLE_DIRS := $(dir $(wildcard examples/**/Doxyfile))
EXAMPLE_OUTPUTS := $(addprefix $(DOXYGEN_BUILD_DIR)/,$(addsuffix xml,$(EXAMPLE_DIRS)))

define EXAMPLE_template
$(DOXYGEN_BUILD_DIR)/$(1): $(DOXYGEN_BUILD_DIR)
	mkdir -p $(DOXYGEN_BUILD_DIR)/$(1)

$(DOXYGEN_BUILD_DIR)/$(1)xml: $(DOXYGEN_BUILD_DIR)/$(1) $(filter-out %.adoc,$(wildcard $(1)/*))
	. $(BUILD_DIR)/doxygen-$(LATEST_DOXYGEN_VERSION)/activate_run.sh; cd $(1) && OUTPUT_DIR=$(DOXYGEN_BUILD_DIR)/$(1) doxygen
endef

$(foreach example_dir,$(EXAMPLE_DIRS),$(eval $(call EXAMPLE_template,$(example_dir))))

ADOC_IN_FILES := $(wildcard *.adoc) $(wildcard **/*.adoc) $(wildcard examples/**/*.adoc)
ADOC_OUT_FILES := $(patsubst %.adoc,%.html,$(addprefix $(DOC_BUILD_DIR)/output/, $(ADOC_IN_FILES)))

$(ADOC_OUT_FILES): $(ADOC_IN_FILES) $(DOC_BUILD_DIR)/asciidoxy $(CURDIR)/asciidoxy.toml $(CURDIR)/copy $(DOXYGEN_BUILD_DIR)/asciidoxy/xml $(EXAMPLE_OUTPUTS)
	asciidoxy index.adoc \
		--base-dir . \
		--build-dir $(DOC_BUILD_DIR)/asciidoxy \
		--destination-dir $(DOC_BUILD_DIR)/output \
		--spec-file asciidoxy.toml \
		--debug $(MULTIPAGE) \
		-a linkcss
