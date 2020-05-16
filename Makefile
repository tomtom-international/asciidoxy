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

.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python3 -c "$$BROWSER_PYSCRIPT"

help:
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test clean-docker ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -path ./.venv -prune -o -name '*.egg-info' -exec rm -rf {} +
	find . -path ./.venv -prune -o -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

clean-test: ## remove test and coverage artifacts
	rm -rf .tox/
	rm -f .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache
	rm -rf test_results
	rm -rf .mypy_cache
	find . -name '.asciidoxy.*' -exec rm -rf {} +

clean-docker: ## remove docker build artifacts
	rm -rf docker/.gradle
	rm -rf docker/build
	rm -rf docker/src/main/docker/dist

lint: ## check style with flake8
	flake8 asciidoxy tests

type-check: ## Check typing with mypy
	mypy asciidoxy

test: ## run tests quickly with the default Python
	pytest

test-all: ## run tests on every Python version with tox
	tox -s

coverage: ## check code coverage quickly with the default Python
	coverage run --source asciidoxy -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python3 setup.py sdist
	python3 setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python3 setup.py install

virtualenv: ## set up a development environment
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements_dev.txt
	. .venv/bin/activate && python3 setup.py develop

docker: dist ## build the docker image
	cd docker && ./gradlew build

format: ## format the code
	yapf -r -i -p setup.py asciidoxy tests

docs: ## generate documentation
	cp -r tests/source_code documentation/source_code
	mkdir -p documentation/copy
	cp CHANGELOG.adoc documentation/copy/
	mkdir -p build/doc/doxygen
	mkdir -p build/doc/asciidoxy
	cd documentation && doxygen
	cd documentation && asciidoxy index.adoc \
		--build-dir ../build/doc/asciidoxy \
		--destination-dir ../build/doc/output \
		--spec-file asciidoxy.toml \
		--debug --multi-page \
		-a linkcss
