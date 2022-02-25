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
"""Tests for collecting source files."""

from pathlib import Path

import pytest
from aiohttp import web

from asciidoxy.packaging.collect import (
    DownloadError,
    HttpPackageSpec,
    InvalidPackageError,
    LocalPackageSpec,
    SpecificationError,
    collect,
    specs_from_file,
    versions_from_file,
)

from ..shared import ProgressMock


async def start_server(aiohttp_server, *routes):
    app = web.Application()
    app.add_routes(routes)
    return await aiohttp_server(app)


async def xml_file_response(request):
    return web.FileResponse(Path(__file__).parent.parent.parent / "data" / "xml.tar.gz")


async def include_file_response(request):
    return web.FileResponse(Path(__file__).parent.parent.parent / "data" / "adoc.tar.gz")


async def package_file_response(request):
    return web.FileResponse(Path(__file__).parent.parent.parent / "data" / "package.tar.gz")


async def corrupt_package_file_response(request):
    return web.FileResponse(Path(__file__).parent.parent.parent / "data" / "corrupt_package.tar.gz")


async def old_style_package_file_response(request):
    return web.FileResponse(
        Path(__file__).parent.parent.parent / "data" / "old_style_package.tar.gz")


async def error404_response(request):
    return web.Response(status=404)


async def text_response(request):
    return web.Response(text="normal text instead of a file")


async def test_http_package__contents_toml(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server, web.get("/test/1.0.0/package",
                                                        package_file_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.file_names = ["package"]

    packages = await collect([spec], tmp_path)

    assert len(packages) == 1
    pkg = packages[0]
    assert pkg.name == "package"
    assert pkg.reference_type == "doxygen"

    assert pkg.reference_dir == tmp_path / "test" / "1.0.0" / "xml"
    assert pkg.reference_dir.is_dir()
    assert (pkg.reference_dir / "content.xml").is_file()

    assert pkg.adoc_src_dir == tmp_path / "test" / "1.0.0" / "adoc"
    assert pkg.adoc_src_dir.is_dir()
    assert (pkg.adoc_src_dir / "content.adoc").is_file()

    assert pkg.adoc_image_dir == tmp_path / "test" / "1.0.0" / "images"
    assert pkg.adoc_image_dir.is_dir()
    assert (pkg.adoc_image_dir / "picture.png").is_file()

    assert pkg.adoc_root_doc == tmp_path / "test" / "1.0.0" / "adoc" / "content.adoc"
    assert pkg.adoc_root_doc.is_file()


async def test_http_package__contents_toml__spec_dirs_ignored(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server, web.get("/test/1.0.0/package",
                                                        package_file_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.file_names = ["package"]

    packages = await collect([spec], tmp_path)

    assert len(packages) == 1
    pkg = packages[0]
    assert pkg.name == "package"
    assert pkg.reference_type == "doxygen"

    assert pkg.reference_dir == tmp_path / "test" / "1.0.0" / "xml"
    assert pkg.reference_dir.is_dir()
    assert (pkg.reference_dir / "content.xml").is_file()

    assert pkg.adoc_src_dir == tmp_path / "test" / "1.0.0" / "adoc"
    assert pkg.adoc_src_dir.is_dir()
    assert (pkg.adoc_src_dir / "content.adoc").is_file()

    assert pkg.adoc_image_dir == tmp_path / "test" / "1.0.0" / "images"
    assert pkg.adoc_image_dir.is_dir()
    assert (pkg.adoc_image_dir / "picture.png").is_file()

    assert pkg.adoc_root_doc == tmp_path / "test" / "1.0.0" / "adoc" / "content.adoc"
    assert pkg.adoc_root_doc.is_file()


async def test_http_package__contents_toml__missing(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server,
                                web.get("/test/1.0.0/package", old_style_package_file_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.file_names = ["package"]

    with pytest.raises(InvalidPackageError):
        await collect([spec], tmp_path)
    assert not (tmp_path / "test" / "1.0.0").exists()


async def test_http_package__contents_toml__corrupt(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server,
                                web.get("/test/1.0.0/package", corrupt_package_file_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.file_names = ["package"]

    with pytest.raises(InvalidPackageError):
        await collect([spec], tmp_path)
    assert not (tmp_path / "test" / "1.0.0").exists()


async def test_http_package__cache_corrupt(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server, web.get("/test/1.0.0/package",
                                                        package_file_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.file_names = ["package"]

    (tmp_path / "test" / "1.0.0").mkdir(parents=True)
    (tmp_path / "test" / "1.0.0" / "contents.toml").touch()

    packages = await collect([spec], tmp_path)

    assert len(packages) == 1
    pkg = packages[0]
    assert pkg.name == "package"
    assert pkg.reference_type == "doxygen"

    assert pkg.reference_dir == tmp_path / "test" / "1.0.0" / "xml"
    assert pkg.reference_dir.is_dir()
    assert (pkg.reference_dir / "content.xml").is_file()

    assert pkg.adoc_src_dir == tmp_path / "test" / "1.0.0" / "adoc"
    assert pkg.adoc_src_dir.is_dir()
    assert (pkg.adoc_src_dir / "content.adoc").is_file()

    assert pkg.adoc_image_dir == tmp_path / "test" / "1.0.0" / "images"
    assert pkg.adoc_image_dir.is_dir()
    assert (pkg.adoc_image_dir / "picture.png").is_file()

    assert pkg.adoc_root_doc == tmp_path / "test" / "1.0.0" / "adoc" / "content.adoc"
    assert pkg.adoc_root_doc.is_file()


async def test_http_package_error404(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server, web.get("/test/1.0.0/error", error404_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.file_names = ["error"]

    with pytest.raises(DownloadError):
        await collect([spec], tmp_path)


async def test_http_package_not_a_tarfile(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server, web.get("/test/1.0.0/text", text_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.file_names = ["text"]

    with pytest.raises(DownloadError):
        await collect([spec], tmp_path)
    assert not (tmp_path / "test" / "1.0.0").exists()


async def test_http_package_name_interpolation_in_file_names(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server, web.get("/test/1.0.0/test", xml_file_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.file_names = ["{name}"]

    await collect([spec], tmp_path)

    assert (tmp_path / "test" / "1.0.0" / "xml" / "content.xml").is_file()


async def test_http_package_version_interpolation_in_file_names(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server,
                                web.get("/test/1.0.0/documentation-1.0.0", xml_file_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.file_names = ["documentation-{version}"]

    await collect([spec], tmp_path)

    assert (tmp_path / "test" / "1.0.0" / "xml" / "content.xml").is_file()


async def test_http_package_version_and_name_interpolation_in_file_names(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server, web.get("/test/1.0.0/test-1.0.0",
                                                        xml_file_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.file_names = ["{name}-{version}"]

    await collect([spec], tmp_path)

    assert (tmp_path / "test" / "1.0.0" / "xml" / "content.xml").is_file()


async def test_local_package__contents_toml(tmp_path):
    output_dir = tmp_path / "output"
    input_dir = tmp_path / "input"

    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "xml").mkdir()
    (input_dir / "adoc").mkdir()
    (input_dir / "images").mkdir()
    (input_dir / "contents.toml").write_text("""\
[package]
name = "package"

[reference]
type = "doxygen"
dir = "xml"

[asciidoc]
src_dir = "adoc"
image_dir = "images"
""")

    spec = LocalPackageSpec("test", input_dir)

    packages = await collect([spec], output_dir)
    assert len(packages) == 1

    pkg = packages[0]
    assert pkg.name == "package"
    assert pkg.reference_type == "doxygen"

    assert pkg.reference_dir == input_dir / "xml"
    assert pkg.adoc_src_dir == input_dir / "adoc"
    assert pkg.adoc_image_dir == input_dir / "images"


async def test_progress_report(tmp_path):
    output_dir = tmp_path / "output"
    input_dir = tmp_path / "input"

    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "xml").mkdir()
    (input_dir / "contents.toml").write_text("""\
[package]
name = "package"

[reference]
type = "doxygen"
dir = "xml"
""")

    spec = LocalPackageSpec("test", input_dir)
    progress_mock = ProgressMock()

    packages = await collect([spec, spec, spec], output_dir, progress=progress_mock)
    assert len(packages) == 3
    assert progress_mock.ready == 3


def test_versions_from_file(tmp_path):
    version_file = tmp_path / "versions.csv"
    version_file.write_text("""Component name,Version
boost,1.70.0
server,13.2.3
client,3.18.4
""")

    versions = versions_from_file(version_file)
    assert versions == {"boost": "1.70.0", "server": "13.2.3", "client": "3.18.4"}


def test_specs_from_file__http_package(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]
version = "1.0.0"
""")

    specs = specs_from_file(spec_file)
    assert len(specs) == 1

    spec = specs[0]
    assert spec.name == "test"
    assert isinstance(spec, HttpPackageSpec)
    assert spec.url_template == "https://example.com/{version}"
    assert spec.file_names == ["xml.tar.gz"]
    assert spec.version == "1.0.0"


def test_specs_from_file__http_package__with_version_file(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]
""")

    version_file = tmp_path / "versions.csv"
    version_file.write_text("""Component name,Version
test0,3.0.0
test,1.5.8
test43,1.2.3
""")

    specs = specs_from_file(spec_file, version_file)
    assert len(specs) == 1

    spec = specs[0]
    assert spec.name == "test"
    assert isinstance(spec, HttpPackageSpec)
    assert spec.url_template == "https://example.com/{version}"
    assert spec.file_names == ["xml.tar.gz"]
    assert spec.version == "1.5.8"


def test_specs_from_file__http_package__with_version_file__spec_override(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]
version = "15.2.1"
""")

    version_file = tmp_path / "versions.csv"
    version_file.write_text("""Component name,Version
test0,3.0.0
test,1.5.8
test43,1.2.3
""")

    specs = specs_from_file(spec_file, version_file)
    assert len(specs) == 1

    spec = specs[0]
    assert spec.name == "test"
    assert isinstance(spec, HttpPackageSpec)
    assert spec.url_template == "https://example.com/{version}"
    assert spec.file_names == ["xml.tar.gz"]
    assert spec.version == "15.2.1"


def test_specs_from_file__http_package__with_version_file__version_missing(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]
""")

    version_file = tmp_path / "versions.csv"
    version_file.write_text("""Component name,Version
test0,3.0.0
test43,1.2.3
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file, version_file)


def test_specs_from_file__http_package__no_url_template(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
file_names = [ "xml.tar.gz" ]
version = "1.0.0"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__http_package__no_file_names(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
url_template = "https://example.com/{version}"
version = "1.0.0"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__http_package__invalid_file_names(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
url_template = "https://example.com/{version}"
file_names = "xml.tar.gz"
version = "1.0.0"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__http_package__no_version(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__local_package(tmp_path):
    spec_file = tmp_path / "spec.toml"
    package_dir = tmp_path / "package"
    spec_file.write_text(f"""
[packages]

[packages.test]
type = "local"
package_dir = "{package_dir}"
""")

    specs = specs_from_file(spec_file)
    assert len(specs) == 1

    spec = specs[0]
    assert spec.name == "test"
    assert isinstance(spec, LocalPackageSpec)
    assert spec.package_dir == package_dir


def test_specs_from_file__local_package_no_package_dir(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "local"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__no_type(tmp_path):
    spec_file = tmp_path / "spec.toml"
    package_dir = tmp_path / "package"
    spec_file.write_text(f"""
[packages]

[packages.test]
file_names = [ "xml.tar.gz" ]
url_template = "https://example.com/{{version}}"
version = "1.0.0"
package_dir = "{package_dir}"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__source(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[sources]

[sources.http]
type = "http"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]


[packages]

[packages.test]
source = "http"
version = "1.0.0"
""")

    specs = specs_from_file(spec_file)
    assert len(specs) == 1

    spec = specs[0]
    assert spec.name == "test"
    assert isinstance(spec, HttpPackageSpec)
    assert spec.url_template == "https://example.com/{version}"
    assert spec.file_names == ["xml.tar.gz"]
    assert spec.version == "1.0.0"


def test_specs_from_file__source__override_partial(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[sources]

[sources.http]
type = "http"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]


[packages]

[packages.test]
source = "http"
version = "1.0.0"
""")

    specs = specs_from_file(spec_file)
    assert len(specs) == 1

    spec = specs[0]
    assert spec.name == "test"
    assert isinstance(spec, HttpPackageSpec)
    assert spec.url_template == "https://example.com/{version}"
    assert spec.file_names == ["xml.tar.gz"]
    assert spec.version == "1.0.0"


def test_specs_from_file__source__unknown(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[sources]


[packages]

[packages.test]
source = "http"
version = "1.0.0"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__name_and_version_interpolation(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[sources]

[sources.http]
type = "http"
url_template = "https://example.com/{version}"
file_names = [ "{name}-{version}.tar.gz" ]


[packages]

[packages.test]
source = "http"
version = "1.0.0"
""")

    specs = specs_from_file(spec_file)
    assert len(specs) == 1

    spec = specs[0]
    assert spec.name == "test"
    assert isinstance(spec, HttpPackageSpec)
    assert spec.url_template == "https://example.com/{version}"
    assert spec.file_names == ["{name}-{version}.tar.gz"]
    assert spec.version == "1.0.0"
