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
"""
Tests for collecting source files.
"""

import pytest

from aiohttp import web
from pathlib import Path

from asciidoxy.collect import (DownloadError, InvalidPackageError, HttpPackageSpec,
                               SpecificationError, LocalPackageSpec, collect, specs_from_file,
                               versions_from_file)

from .shared import ProgressMock


async def start_server(aiohttp_server, *routes):
    app = web.Application()
    app.add_routes(routes)
    return await aiohttp_server(app)


async def xml_file_response(request):
    return web.FileResponse(Path(__file__).parent / "data" / "xml.tar.gz")


async def include_file_response(request):
    return web.FileResponse(Path(__file__).parent / "data" / "adoc.tar.gz")


async def error404_response(request):
    return web.Response(status=404)


async def text_response(request):
    return web.Response(text="normal text instead of a file")


async def test_http_package_xml_only(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server, web.get("/test/1.0.0/xml", xml_file_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.xml_subdir = "xml"
    spec.include_subdir = "adoc"
    spec.file_names = ["xml"]

    packages = await collect([spec], tmp_path)

    assert len(packages) == 1
    pkg = packages[0]
    assert pkg.name == "test"
    assert len(pkg.xml_dirs) == 1
    assert len(pkg.include_dirs) == 0

    xml_dir = pkg.xml_dirs[0]
    assert xml_dir.is_dir()
    assert (xml_dir / "content.xml").is_file()

    assert (tmp_path / "test" / "1.0.0" / "xml").is_dir()
    assert (tmp_path / "test" / "1.0.0" / "xml" / "content.xml").is_file()


async def test_http_package_include_only(aiohttp_server, tmp_path):
    server = await start_server(aiohttp_server, web.get("/test/1.0.0/include",
                                                        include_file_response))

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.xml_subdir = "xml"
    spec.include_subdir = "adoc"
    spec.file_names = ["include"]

    packages = await collect([spec], tmp_path)

    assert len(packages) == 1
    pkg = packages[0]
    assert pkg.name == "test"
    assert len(pkg.xml_dirs) == 0
    assert len(pkg.include_dirs) == 1

    include_dir = pkg.include_dirs[0]
    assert include_dir.is_dir()
    assert (include_dir / "content.adoc").is_file()

    assert (tmp_path / "test" / "1.0.0" / "adoc").is_dir()
    assert (tmp_path / "test" / "1.0.0" / "adoc" / "content.adoc").is_file()


async def test_http_package_xml_and_include(aiohttp_server, tmp_path):
    server = await start_server(
        aiohttp_server,
        web.get("/test/1.0.0/include", include_file_response),
        web.get("/test/1.0.0/xml", xml_file_response),
    )

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.xml_subdir = "xml"
    spec.include_subdir = "adoc"
    spec.file_names = ["include", "xml"]

    packages = await collect([spec], tmp_path)

    assert len(packages) == 1
    pkg = packages[0]
    assert pkg.name == "test"
    assert len(pkg.xml_dirs) == 1
    assert len(pkg.include_dirs) == 1

    xml_dir = pkg.xml_dirs[0]
    assert xml_dir.is_dir()
    assert (xml_dir / "content.xml").is_file()

    assert (tmp_path / "test" / "1.0.0" / "xml").is_dir()
    assert (tmp_path / "test" / "1.0.0" / "xml" / "content.xml").is_file()

    include_dir = pkg.include_dirs[0]
    assert include_dir.is_dir()
    assert (include_dir / "content.adoc").is_file()

    assert (tmp_path / "test" / "1.0.0" / "adoc").is_dir()
    assert (tmp_path / "test" / "1.0.0" / "adoc" / "content.adoc").is_file()


async def test_http_package_subdirs_not_matched(aiohttp_server, tmp_path):
    server = await start_server(
        aiohttp_server,
        web.get("/test/1.0.0/include", include_file_response),
        web.get("/test/1.0.0/xml", xml_file_response),
    )

    spec = HttpPackageSpec("test", "1.0.0",
                           f"http://localhost:{server.port}/{{name}}/{{version}}/{{file_name}}")
    spec.xml_subdir = "doxygen"
    spec.include_subdir = "include"
    spec.file_names = ["include", "xml"]

    with pytest.raises(InvalidPackageError):
        await collect([spec], tmp_path)


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


async def test_local_package_xml_and_include(tmp_path):
    output_dir = tmp_path / "output"
    input_dir = tmp_path / "input"

    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "xml").mkdir()
    (input_dir / "adoc").mkdir()

    spec = LocalPackageSpec("test", input_dir)
    spec.xml_subdir = "xml"
    spec.include_subdir = "adoc"

    packages = await collect([spec], output_dir)
    assert len(packages) == 1

    pkg = packages[0]
    assert pkg.name == "test"
    assert len(pkg.xml_dirs) == 1
    assert len(pkg.include_dirs) == 1

    assert (input_dir / "xml") in pkg.xml_dirs
    assert (input_dir / "adoc") in pkg.include_dirs


async def test_local_package_include_only(tmp_path):
    output_dir = tmp_path / "output"
    input_dir = tmp_path / "input"

    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "adoc").mkdir()

    spec = LocalPackageSpec("test", input_dir)
    spec.xml_subdir = "xml"
    spec.include_subdir = "adoc"

    packages = await collect([spec], output_dir)
    assert len(packages) == 1

    pkg = packages[0]
    assert pkg.name == "test"
    assert len(pkg.xml_dirs) == 0
    assert len(pkg.include_dirs) == 1

    assert (input_dir / "adoc") in pkg.include_dirs


async def test_local_package_xml_only(tmp_path):
    output_dir = tmp_path / "output"
    input_dir = tmp_path / "input"

    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "xml").mkdir()

    spec = LocalPackageSpec("test", input_dir)
    spec.xml_subdir = "xml"
    spec.include_subdir = "adoc"

    packages = await collect([spec], output_dir)
    assert len(packages) == 1

    pkg = packages[0]
    assert pkg.name == "test"
    assert len(pkg.xml_dirs) == 1
    assert len(pkg.include_dirs) == 0

    assert (input_dir / "xml") in pkg.xml_dirs


async def test_local_package_subdirs_not_matched(tmp_path):
    output_dir = tmp_path / "output"
    input_dir = tmp_path / "input"

    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "doxygen").mkdir()
    (input_dir / "include").mkdir()

    spec = LocalPackageSpec("test", input_dir)
    spec.xml_subdir = "xml"
    spec.include_subdir = "adoc"

    with pytest.raises(InvalidPackageError):
        await collect([spec], output_dir)


async def test_progress_report(tmp_path):
    output_dir = tmp_path / "output"
    input_dir = tmp_path / "input"

    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "xml").mkdir()

    spec = LocalPackageSpec("test", input_dir)
    spec.xml_subdir = "xml"
    spec.include_subdir = "adoc"

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
xml_subdir = "xml"
include_subdir = "include"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]
version = "1.0.0"
""")

    specs = specs_from_file(spec_file)
    assert len(specs) == 1

    spec = specs[0]
    assert spec.name == "test"
    assert isinstance(spec, HttpPackageSpec)
    assert spec.xml_subdir == "xml"
    assert spec.include_subdir == "include"
    assert spec.url_template == "https://example.com/{version}"
    assert spec.file_names == ["xml.tar.gz"]
    assert spec.version == "1.0.0"


def test_specs_from_file__http_package__with_version_file(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
xml_subdir = "xml"
include_subdir = "include"
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
    assert spec.xml_subdir == "xml"
    assert spec.include_subdir == "include"
    assert spec.url_template == "https://example.com/{version}"
    assert spec.file_names == ["xml.tar.gz"]
    assert spec.version == "1.5.8"


def test_specs_from_file__http_package__with_version_file__spec_override(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
xml_subdir = "xml"
include_subdir = "include"
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
    assert spec.xml_subdir == "xml"
    assert spec.include_subdir == "include"
    assert spec.url_template == "https://example.com/{version}"
    assert spec.file_names == ["xml.tar.gz"]
    assert spec.version == "15.2.1"


def test_specs_from_file__http_package__with_version_file__version_missing(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
xml_subdir = "xml"
include_subdir = "include"
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


def test_specs_from_file__http_package__no_xml_subdir(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
include_subdir = "include"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]
version = "1.0.0"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__http_package__no_include_subdir(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
xml_subdir = "xml"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]
version = "1.0.0"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__http_package__no_url_template(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[packages]

[packages.test]
type = "http"
xml_subdir = "xml"
include_subdir = "include"
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
xml_subdir = "xml"
include_subdir = "include"
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
xml_subdir = "xml"
include_subdir = "include"
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
xml_subdir = "xml"
include_subdir = "include"
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
xml_subdir = "xml"
include_subdir = "include"
package_dir = "{package_dir}"
""")

    specs = specs_from_file(spec_file)
    assert len(specs) == 1

    spec = specs[0]
    assert spec.name == "test"
    assert isinstance(spec, LocalPackageSpec)
    assert spec.xml_subdir == "xml"
    assert spec.include_subdir == "include"
    assert spec.package_dir == package_dir


def test_specs_from_file__local_package_no_xml_subdir(tmp_path):
    spec_file = tmp_path / "spec.toml"
    package_dir = tmp_path / "package"
    spec_file.write_text(f"""
[packages]

[packages.test]
type = "local"
include_subdir = "include"
package_dir = "{package_dir}"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__local_package_no_include_subdir(tmp_path):
    spec_file = tmp_path / "spec.toml"
    package_dir = tmp_path / "package"
    spec_file.write_text(f"""
[packages]

[packages.test]
type = "local"
xml_subdir = "xml"
package_dir = "{package_dir}"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__local_package_no_package_dir(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text(f"""
[packages]

[packages.test]
type = "local"
xml_subdir = "xml"
include_subdir = "include"
""")

    with pytest.raises(SpecificationError):
        specs_from_file(spec_file)


def test_specs_from_file__no_type(tmp_path):
    spec_file = tmp_path / "spec.toml"
    package_dir = tmp_path / "package"
    spec_file.write_text(f"""
[packages]

[packages.test]
xml_subdir = "xml"
include_subdir = "include"
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
xml_subdir = "xml"
include_subdir = "include"
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
    assert spec.xml_subdir == "xml"
    assert spec.include_subdir == "include"
    assert spec.url_template == "https://example.com/{version}"
    assert spec.file_names == ["xml.tar.gz"]
    assert spec.version == "1.0.0"


def test_specs_from_file__source__override_partial(tmp_path):
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text("""
[sources]

[sources.http]
type = "http"
xml_subdir = "xml"
include_subdir = "include"
url_template = "https://example.com/{version}"
file_names = [ "xml.tar.gz" ]


[packages]

[packages.test]
source = "http"
xml_subdir = "doxygen"
include_subdir = "adoc"
version = "1.0.0"
""")

    specs = specs_from_file(spec_file)
    assert len(specs) == 1

    spec = specs[0]
    assert spec.name == "test"
    assert isinstance(spec, HttpPackageSpec)
    assert spec.xml_subdir == "doxygen"
    assert spec.include_subdir == "adoc"
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
