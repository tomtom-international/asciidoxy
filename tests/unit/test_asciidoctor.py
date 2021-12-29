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
"""Test generating the AsciiDoctor runner."""

from asciidoxy import asciidoctor


def test_write_asciidoctor_runner__singlepage(default_config, document, package_manager):
    docs = [
        document,
        document.with_relative_path("included.adoc"),
        document.with_relative_path("embedded.adoc")
    ]
    docs[0].is_root = True
    docs[0].include(docs[1])
    docs[0].embed(docs[2])

    runner_path = asciidoctor.write_asciidoctor_runner(docs, default_config, package_manager)
    assert runner_path.is_file()
    work_dir = package_manager.work_dir
    out_dir = default_config.destination_dir
    assert runner_path.read_text() == f"""\
require 'asciidoctor'
Asciidoctor.convert_file '{work_dir}/input_file.adoc', to_file: '{out_dir}/input_file.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images'
logger = Asciidoctor::LoggerManager.logger
exit 1 if (logger.respond_to? :max_severity) &&
  logger.max_severity &&
  logger.max_severity >= (::Logger::Severity.const_get 'FATAL')
"""


def test_write_asciidoctor_runner__multipage(default_config, document, package_manager):
    docs = [
        document,
        document.with_relative_path("included.adoc"),
        document.with_relative_path("embedded.adoc")
    ]
    docs[0].is_root = True
    docs[0].include(docs[1])
    docs[0].embed(docs[2])
    default_config.multipage = True

    runner_path = asciidoctor.write_asciidoctor_runner(docs, default_config, package_manager)
    assert runner_path.is_file()
    work_dir = package_manager.work_dir
    out_dir = default_config.destination_dir
    assert runner_path.read_text() == f"""\
require 'asciidoctor'
Asciidoctor.convert_file '{work_dir}/input_file.adoc', to_file: '{out_dir}/input_file.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage'
Asciidoctor.convert_file '{work_dir}/included.adoc', to_file: '{out_dir}/included.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage'
logger = Asciidoctor::LoggerManager.logger
exit 1 if (logger.respond_to? :max_severity) &&
  logger.max_severity &&
  logger.max_severity >= (::Logger::Severity.const_get 'FATAL')
"""


def test_write_asciidoctor_runner__attributes(default_config, document, package_manager):
    docs = [
        document,
        document.with_relative_path("included.adoc"),
        document.with_relative_path("embedded.adoc")
    ]
    docs[0].is_root = True
    docs[0].include(docs[1])
    docs[0].embed(docs[2])
    default_config.multipage = True
    default_config.attribute = ["sectnums", "version=12"]

    runner_path = asciidoctor.write_asciidoctor_runner(docs, default_config, package_manager)
    assert runner_path.is_file()
    work_dir = package_manager.work_dir
    out_dir = default_config.destination_dir
    assert runner_path.read_text() == f"""\
require 'asciidoctor'
Asciidoctor.convert_file '{work_dir}/input_file.adoc', to_file: '{out_dir}/input_file.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage sectnums version=12'
Asciidoctor.convert_file '{work_dir}/included.adoc', to_file: '{out_dir}/included.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage sectnums version=12'
logger = Asciidoctor::LoggerManager.logger
exit 1 if (logger.respond_to? :max_severity) &&
  logger.max_severity &&
  logger.max_severity >= (::Logger::Severity.const_get 'FATAL')
"""


def test_write_asciidoctor_runner__plugins(default_config, document, package_manager):
    docs = [
        document,
        document.with_relative_path("included.adoc"),
        document.with_relative_path("embedded.adoc")
    ]
    docs[0].is_root = True
    docs[0].include(docs[1])
    docs[0].embed(docs[2])
    default_config.multipage = True
    default_config.require = ["asciidoctor-diagram", "asciidoctor-awesome"]

    runner_path = asciidoctor.write_asciidoctor_runner(docs, default_config, package_manager)
    assert runner_path.is_file()
    work_dir = package_manager.work_dir
    out_dir = default_config.destination_dir
    assert runner_path.read_text() == f"""\
require 'asciidoctor'
require 'asciidoctor-diagram'
require 'asciidoctor-awesome'
Asciidoctor.convert_file '{work_dir}/input_file.adoc', to_file: '{out_dir}/input_file.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage'
Asciidoctor.convert_file '{work_dir}/included.adoc', to_file: '{out_dir}/included.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage'
logger = Asciidoctor::LoggerManager.logger
exit 1 if (logger.respond_to? :max_severity) &&
  logger.max_severity &&
  logger.max_severity >= (::Logger::Severity.const_get 'FATAL')
"""


def test_write_asciidoctor_runner__safe_mode(default_config, document, package_manager):
    docs = [
        document,
        document.with_relative_path("included.adoc"),
        document.with_relative_path("embedded.adoc")
    ]
    docs[0].is_root = True
    docs[0].include(docs[1])
    docs[0].embed(docs[2])
    default_config.multipage = True
    default_config.safe_mode = "server"

    runner_path = asciidoctor.write_asciidoctor_runner(docs, default_config, package_manager)
    assert runner_path.is_file()
    work_dir = package_manager.work_dir
    out_dir = default_config.destination_dir
    assert runner_path.read_text() == f"""\
require 'asciidoctor'
Asciidoctor.convert_file '{work_dir}/input_file.adoc', to_file: '{out_dir}/input_file.html', safe: :server, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage'
Asciidoctor.convert_file '{work_dir}/included.adoc', to_file: '{out_dir}/included.html', safe: :server, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage'
logger = Asciidoctor::LoggerManager.logger
exit 1 if (logger.respond_to? :max_severity) &&
  logger.max_severity &&
  logger.max_severity >= (::Logger::Severity.const_get 'FATAL')
"""


def test_write_asciidoctor_runner__doctype(default_config, document, package_manager):
    docs = [
        document,
        document.with_relative_path("included.adoc"),
        document.with_relative_path("embedded.adoc")
    ]
    docs[0].is_root = True
    docs[0].include(docs[1])
    docs[0].embed(docs[2])
    default_config.multipage = True
    default_config.doctype = "book"

    runner_path = asciidoctor.write_asciidoctor_runner(docs, default_config, package_manager)
    assert runner_path.is_file()
    work_dir = package_manager.work_dir
    out_dir = default_config.destination_dir
    assert runner_path.read_text() == f"""\
require 'asciidoctor'
Asciidoctor.convert_file '{work_dir}/input_file.adoc', to_file: '{out_dir}/input_file.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage', doctype: 'book'
Asciidoctor.convert_file '{work_dir}/included.adoc', to_file: '{out_dir}/included.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage', doctype: 'book'
logger = Asciidoctor::LoggerManager.logger
exit 1 if (logger.respond_to? :max_severity) &&
  logger.max_severity &&
  logger.max_severity >= (::Logger::Severity.const_get 'FATAL')
"""


def test_write_asciidoctor_runner__failure_level(default_config, document, package_manager):
    docs = [
        document,
        document.with_relative_path("included.adoc"),
        document.with_relative_path("embedded.adoc")
    ]
    docs[0].is_root = True
    docs[0].include(docs[1])
    docs[0].embed(docs[2])
    default_config.multipage = True
    default_config.failure_level = "ERROR"

    runner_path = asciidoctor.write_asciidoctor_runner(docs, default_config, package_manager)
    assert runner_path.is_file()
    work_dir = package_manager.work_dir
    out_dir = default_config.destination_dir
    assert runner_path.read_text() == f"""\
require 'asciidoctor'
Asciidoctor.convert_file '{work_dir}/input_file.adoc', to_file: '{out_dir}/input_file.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage'
Asciidoctor.convert_file '{work_dir}/included.adoc', to_file: '{out_dir}/included.html', safe: :unsafe, backend: 'html5', mkdirs: true, basedir: '{work_dir}', attributes: 'imagesdir@=images multipage'
logger = Asciidoctor::LoggerManager.logger
exit 1 if (logger.respond_to? :max_severity) &&
  logger.max_severity &&
  logger.max_severity >= (::Logger::Severity.const_get 'ERROR')
"""
