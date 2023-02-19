# syntax=docker/dockerfile:1
FROM alpine:3.17.2

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
RUN PYTHON_DEV_PKGS="gcc g++ python3-dev" \
  && apk add --no-cache $PYTHON_DEV_PKGS \
  && pip3 install --no-cache --upgrade /tmp/*.whl \
  && rm -f /tmp/*.whl \
  && apk del $PYTHON_DEV_PKGS
