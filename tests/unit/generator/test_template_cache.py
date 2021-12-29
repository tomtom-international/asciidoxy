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
"""Test the template cache implementation."""

import pytest

from asciidoxy.generator.cache import TemplateCache
from asciidoxy.generator.errors import TemplateMissingError


def test_template_for__internal__template_available():
    cache = TemplateCache()
    template = cache.template_for("cpp", "class")
    assert template is not None
    assert template.source.startswith("## Copyright (C) 2019, TomTom (http://tomtom.com).")

    assert cache.template_for("cpp", "class") is template


def test_template_for__internal__kind_not_found():
    cache = TemplateCache()
    with pytest.raises(TemplateMissingError):
        cache.template_for("cpp", "klass")


def test_template_for__internal__language_not_found():
    cache = TemplateCache()
    with pytest.raises(TemplateMissingError):
        cache.template_for("smalltalk", "class")


def test_template_for__custom__template_from_custom_has_priority(tmp_path):
    (tmp_path / "cpp").mkdir(parents=True)
    (tmp_path / "cpp" / "class.mako").write_text("Hello world")

    cache = TemplateCache(directories=[str(tmp_path)])
    template = cache.template_for("cpp", "class")
    assert template is not None
    assert template.source.startswith("Hello world")


def test_template_for__custom__template_from_custom_with_custom_name(tmp_path):
    (tmp_path / "cpp").mkdir(parents=True)
    (tmp_path / "cpp" / "myclass.mako").write_text("Hello world")

    cache = TemplateCache(custom_template_dir=tmp_path)
    template = cache.template_for("cpp", "myclass")
    assert template is not None
    assert template.source.startswith("Hello world")


def test_template_for__custom__fallback_to_internal(tmp_path):
    (tmp_path / "cpp").mkdir(parents=True)
    (tmp_path / "cpp" / "class.mako").write_text("Hello world")

    cache = TemplateCache(custom_template_dir=tmp_path)
    template = cache.template_for("cpp", "struct")
    assert template is not None
    assert template.source.startswith("## Copyright (C) 2019, TomTom (http://tomtom.com).")


def test_template_for__custom__kind_not_found(tmp_path):
    (tmp_path / "cpp").mkdir(parents=True)
    (tmp_path / "cpp" / "class.mako").write_text("Hello world")

    cache = TemplateCache(custom_template_dir=tmp_path)
    with pytest.raises(TemplateMissingError):
        cache.template_for("cpp", "klass")


def test_template_for__custom__language_not_found(tmp_path):
    (tmp_path / "cpp").mkdir(parents=True)
    (tmp_path / "cpp" / "class.mako").write_text("Hello world")

    cache = TemplateCache(custom_template_dir=tmp_path)
    with pytest.raises(TemplateMissingError):
        cache.template_for("smalltalk", "class")


def test_cache_dir(tmp_path):
    cache_dir = tmp_path / "cache"
    cache = TemplateCache(cache_dir=cache_dir)
    template = cache.template_for("cpp", "class")
    assert template is not None
    assert template.source.startswith("## Copyright (C) 2019, TomTom (http://tomtom.com).")
    assert (cache_dir / "templates" / "cpp" / "class.mako.py").is_file()
