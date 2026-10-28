# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

AsciiDoxy turns AsciiDoc files into documentation (single page or multipage HTML, PDF, or plain
AsciiDoc). It treats each `.adoc` input as a Mako template: documents call methods on an `api`
object to insert API reference generated from Doxygen XML (C++, Java, Objective-C, Python), and
can transcode elements to other languages (Java→Kotlin, ObjC→Swift). Python 3.7+.

## Commands

Set up the dev environment with `make virtualenv`, then `. .venv/bin/activate`.

- `make unit-test` runs `pytest --numprocesses=auto --maxprocesses=6 tests/unit`
- Single test: `pytest tests/unit/generator/test_generator.py::test_name`; add `-k` or a
  parametrize id such as `-k "1.9.2"` to limit it to one Doxygen version
- `make lint` runs `flake8 asciidoxy tests/unit` (max line length 100)
- `make type-check` runs `mypy asciidoxy`
- `make format` runs `yapf` (config in `.style.yapf`) and `isort` (profile `hug`)
- `make test-all` runs tox over py37–py311 (pytest, flake8 and mypy); run it before a PR
- `pytest --update-expected-results` rewrites the expected `.adoc` output files after a template
  change. Check the diff afterwards for unintended changes.
- `make generate-test-xml` regenerates the Doxygen XML test data for every supported Doxygen
  version (installs Doxygen through conan)
- `make visual-test` renders `tests/visual/*.adoc` with their `.toml` spec files to
  `build/visual-test` for checking by eye
- `make docs` builds the website in `documentation/` with AsciiDoxy itself

## Architecture

The pipeline in `asciidoxy/cli.py:main`:

1. **Packaging** (`asciidoxy/packaging`): `PackageManager` reads the spec file (TOML) and collects
   packages (Doxygen XML, AsciiDoc files, images) from local dirs or remote HTTP archives
   (aiohttp). It also prepares the work directory that the input documents are copied into.
2. **Parsing** (`asciidoxy/parser/doxygen`): `Driver` parses the XML with a language-specific
   `ParserBase` subclass (`cpp.py`, `java.py`, `objc.py`, `python.py`), each with its own
   `LanguageTraits` and `TypeParser`. After loading, `resolve_references` links types across
   files, and `check_references` removes refids that point to missing elements. The result is an
   `ApiReference` (`api_reference.py`) holding `model.py` elements, which supports filtered,
   namespace-aware lookup.
3. **Generation** (`asciidoxy/generator`): `process_adoc` renders every document **twice**.
   `PreprocessingApi` runs first, collecting anchors, inserted elements, and the document tree
   for includes and multipage. Then `_check_links` runs, and `GeneratingApi` renders the real
   output. A new `Api` method must behave correctly in both subclasses: the preprocessing
   variant usually only records state. `ApiProxy.__getattr__` provides dynamic
   `insert_<kind>`/`link_<kind>` methods.
4. **Templates** (`asciidoxy/generator/templates/<lang>/<kind>.mako`): insertion of an element
   picks the Mako template by language and element kind. `helpers.py` and each language's
   helpers module supply the formatting logic. Users can override templates with custom
   template dirs.
5. **Transcoding** (`asciidoxy/transcoder`): `TranscoderBase.transcode` converts model elements
   from a source language when `api.language(lang, source=...)` is set and the element does not
   exist in the target language.
6. **AsciiDoctor** (`asciidoctor.py`): runs the external `asciidoctor` or `asciidoctor-pdf`,
   unless the backend is `adoc`.

`documentation/contributing.adoc` has an architecture section and a guide to adding a
language, but some of its module paths are out of date (`doxygenparser` is now
`asciidoxy/parser/doxygen`, and `asciidoxy/templates` is now `asciidoxy/generator/templates`).

## Test data

- `tests/data/source_code/` holds the source that the Doxygen XML is generated from.
  `tests/data/generated/xml/<doxygen-version>/` holds the generated XML. Fixtures in
  `tests/unit/conftest.py` (`doxygen_version`, `xml_data`, `api_reference`) are parametrized over
  every version directory, so each such test runs once per Doxygen version.
- Expected outputs in `tests/data/adoc/` are per Doxygen version, for example
  `fragments/cpp/class.1.9.2.adoc`, and some also per mode (`.singlepage.` and `.multipage.`).
  A template change usually means updating all of them with `--update-expected-results`.
- Use the `api_reference_set` and `forced_language` fixtures to choose which XML sets a test
  loads. `tests/unit/builders.py` and `matchers.py` provide model builders and assertion
  helpers.

## Conventions

- Docstrings use Google style. Every source file starts with the Apache 2.0 license header.
- Branches: this is `develop-0.8.x`, the maintenance branch for 0.8 releases. PRs with 0.8.x
  fixes target `develop-0.8.x`. `develop` holds 0.9 development (`0.9.0+dev`) and has diverged
  a lot from this branch (for example the model refactor), so do not merge or rebase between them.
  Port fixes by cherry-picking or by reimplementing them. `documentation/contributing.adoc`
  describes the `develop` workflow.
- Releases: a 0.8.x release starts with a "build: start work on version 0.8.x" commit, which
  bumps `asciidoxy/_version.py`. It ends with a "docs: prepare version 0.8.x" commit, which
  renames the unreleased heading in `CHANGELOG.adoc` to the new version (headings use
  `== <version> (<date>)` with `=== Added` and similar subsections). Then `develop-0.8.x` is
  merged into `master` in a "feat: AsciiDoxy 0.8.x" merge commit.
