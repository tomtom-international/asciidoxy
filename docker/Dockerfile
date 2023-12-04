# Copyright (C) 2019, TomTom (http://tomtom.com).
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
# syntax=docker/dockerfile:1
FROM alpine:3.18.5

RUN apk add --no-cache \
  bash \
  doxygen \
  font-freefont \
  graphviz \
  plantuml \
  python3 \
  ruby

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade \
  pip \
  setuptools \
  wheel

RUN gem install \
  asciidoctor \
  asciidoctor-diagram \
  asciidoctor-pdf \
  asciidoctor-rouge

COPY *.whl /tmp/
RUN PYTHON_DEV_PKGS="gcc g++ python3-dev libffi-dev" \
  && apk add --no-cache $PYTHON_DEV_PKGS \
  && pip3 install --no-cache --upgrade /tmp/*.whl \
  && rm -f /tmp/*.whl \
  && apk del $PYTHON_DEV_PKGS
