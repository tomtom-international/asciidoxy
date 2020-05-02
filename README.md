# AsciiDoxy

AsciiDoxy generates API documentation from Doxygen XML output to AsciiDoc.

Supported languages:
- C++
- Java
- Objective C

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project
template.

Before going public on GitHub, several TomTommers contributed to the internal version of AsciiDoxy.
Many thanks to:
- Andy Salter
- Arkadiusz Skalski
- Lukasz Glowcyk
- Nebojsa Mrmak
- Niels van der Schans
- Robert Gernert
- Tomasz Maj

## What does AsciiDoxy do?

In essence AsciiDoxy is a preprocessor for AsciiDoc files. It looks for specific tags in these files
and replaces them with valid AsciiDoc syntax. The information it inserts into the AsciiDoc files
comes from Doxygen XML output.

### 1\. Collects Doxygen XML and include files

Doxygen XML files are collected from remote HTTP servers, from the local file system, or a
combination of both. What files are collected is specified in a package specification file and
optionally a version file. See [Package specification](#package-specification) for details.

The packages can also contain other files that can be included in the documentation. These can be
other AsciiDoc files, images, and other included files. The included AsciiDoc files can alo contain
AsciiDoxy directives.

### 2\. Copies files to an intermediate directory

The input file and all files from the same directory and sub directories will be copied to an
intermediate directory. After this all `adoc` directories from the downloaded archives will also be
copied inside the intermediate directory preserving their directory structure.

### 3\. Parses Doxygen XML

The downloaded Doxygen XML files are parsed into an internal representation that can be converted to
AsciiDoc on demand. References between separate packages are detected and resolved.

The parsing takes the source language into account. Specific cases for each language, like the
format of type specifications, are handled based on the language specified in the Doxygen XML files.

### 4\. Preprocesses Asciidoc files

The input AsciiDoc file is preprocessed using Mako. Mako looks for special syntax, the most common
being `${...}`. Any valid python code can be placed between the braces, and will be executed by Mako.
For more details on the syntax, see the [Mako syntax
documentation](https://docs.makotemplates.org/en/latest/syntax.html).

The code executed by Mako inserts additional AsciiDoc into the file. Methods are provided to use the
information from the Doxygen XML files. See [Usage](#usage) for more details.

Consistency checking is performed to make sure links to, and between, API reference documentation
are valid. Depending on the command line options either a warning or an error is thrown if an
inconsistency is found.

The results of preprocessing are pure AsciiDoc files. They are stored as temporary files next to the
input files inside the intermediate directory. This should preserve all relative links to other
files.

### 5\. Invokes Asciidoctor

When preprocessing is successful, Asciidoctor is invoked to generate single- or multi-paged HTML
output depending on whether the `--multi-page` option was set.

## Installation

The preferred way to install is using pip:

``` bash
pip3 install asciidoxy
```

Alternatively you can directly install the development version:

``` bash
make install
```

## Usage

The minimal invocation takes an input AsciiDoc file and creates the HTML representation:

``` bash
asciidoxy input_file.adoc
```

For more information about command line options:

``` bash
asciidoxy -h
```

In the input AsciiDoc file, you can use any [Mako
syntax](https://docs.makotemplates.org/en/latest/syntax.html). Mako syntax looks like `${...}` where
`...` can contain any valid python code. This python code is executed when the file is processed by
AsciiDoxy.

A special object `api` provides methods to insert API reference documentation and link to its
elements.

### Generating XML using Doxygen

For extracting documentation from source code, AsciiDoxy relies on Doxygen. You are expected to run
Doxygen on your source code, and then provide the path to the generated XML files to AsciiDoxy. It
is recommended to set at least the following non-default settings in your Doxyfile when generating
the XML.

#### C++

    GENERATE_XML           = YES

#### Java

    GENERATE_XML           = YES
    JAVADOC_AUTOBRIEF      = YES
    OPTIMIZE_OUTPUT_JAVA   = YES

#### Objective C

    GENERATE_XML           = YES
    EXTENSION_MAPPING      = h=objective-c

### Package specification

Doxygen XML files and other files to include in the documentation are specified in a package
specification file. The package specification file is in [TOML](https://github.com/toml-lang/toml)
format. It contains 2 main sections: `packages` and `sources`.

#### Packages

The `packages` section is the only mandatory section. It contains a separate subsection for each
package to include. The name of the subsection is the name of the package:

``` toml
[packages]

[packages.package1]
# Specification of `package1`

[packages.package2]
# Specification of `package2`
```

A package has a specific type and based on the type different key/value pairs are required. For all
types of packages the following key/value pairs are required:

  - `type`: The type of the package.

  - `xml_subdir`: Subdirectory in the root of the package in which all Doxygen XML files are stored.

  - `include_subdir`: Subdirectory in the root of the package in which all other include files are
    stored.

Packages of type `local` refer to a local directory. They require the following additional key/value
pairs:

  - `package_dir`: Absolute or relative path to the directory containing the package.

Example:

``` toml
[packages.local_package]
type = "local"
xml_subdir = "xml"
include_subdir = "adoc"
package_dir = "/path/to/my/package/"
```

Packages of type `http` are downloaded from a remote location. They can consist of multiple files,
all of which need to be (compressed) tarballs. Each file can contain XML files, include files, or
both.

The following additional key/value pairs are required:

  - `url_template`: Template for constructing the URL to download the package file from.

  - `file_names`: List of file names making up the package.

The following additional key/value pairs are optional:

  - `version`: Version number of the package.

The `url_template` can contain the following placeholders, that are replaced when creating the URL
to download each package file:

  - `{name}`: Replaced with the name of the package.

  - `{version}`: Replaced with the version of the package.

  - `{file_name}`: Replaced with the file name.

Example:

``` toml
[packages]

[packages.package1]
type = "http"
url_template = "https://example.com/{name}/{version}/{file_name}"
xml_subdir = "xml"
include_subdir = "adoc"
version = "12.3.4"
```

If no `version` is specified for the package, the version is retrieved from a version file. The
version file is a comma separated values file containing pairs of package names and corresponding
versions. It can contain any number of fields, but it is required to have a header containing the
names `Component name` and `Version` for the columns containing these.

Example:

``` text
Component name, Version
package1,3.0.0
package2,4.5.1
```

#### Sources

The `sources` section allows specifying templates for packages. Each template can specify a common
"source" of packages. With a source, settings that are duplicated for many packages can be specified
only once.

A source section can contain every key/value pair that is allowed for a package. Packages can
specify the source they are based on by using the `source` key/value pair.

When a source is used, the key/value pairs of the source and the pacakge are merged. Values for keys
that are present in both the package and the source will be taken from the package. So the package
values override source values.

Example:

``` toml
[sources]

[sources.remote_server]
type = "http"
url_template = "https://example.com/{name}/{version}/{file_name}"
xml_subdir = "xml"
include_subdir = "adoc"

[packages]

[packages.package1]
source = "remote_server"
version = "12.3.4"
```

### Inserting API reference

``` python
${api.insert(<name>[, kind=<kind>][, lang=<language>][, leveloffset])}
${api.insert_<kind>(<name>[, lang=<language>][, leveloffset=<offset>])}

# Examples:
${api.insert("MyNamespace::MyClass")}
${api.insert("com.tomtom.Class", leveloffset="+2")}
${api.insert("com.tomtom.Class", kind="class")}
${api.insert("MyNamespace::FreeFunction", lang="c++")}
${api.insert_class("MyNamespace::MyClass")}
${api.insert_function("MyNamespace::FreeFunction", lang="c++")}
```

Use the `insert` methods to insert API reference documentation at the current location.

  - `name`
    Fully qualified name of the element to insert.

  - `lang`
    Name of the programming language.

  - `kind`
    Kind of element to insert.

  - `leveloffset`
    Offset for the headers in the reference from the top level of the current file. Defaults to +1.

Trying to insert an unknown element will result in an error.

When not specifying the language and kind, AsciiDoxy will try to find the element by name, and
deduce the kind and language. If there are multiple matching elements, an error is raised.

### Filtering what is inserted

By default `api.insert` inserts all contents of the API element. You can control which members,
inner classes, enum values, and exceptions get inserted for every call to `api.insert` or for a
specific call.

To apply a filter for all calls use:

``` python
${api.filter([members=<filter_spec>,]
             [inner_classes=<filter_spec>,]
             [enum_values=<filter_spec>,]
             [exceptions=<filter_spec>])
```

For filtering only on a specific element:

``` python
${api.insert(...,
             [members=<filter_spec>,]
             [inner_classes=<filter_spec>,]
             [enum_values=<filter_spec>,]
             [exceptions=<filter_spec>])
```

A filter specification is either a single string, a list of strings, or a dictionary.

A single string is the same as a list of strings with just one item.

A list of strings defines a set of regular expressions to be applied to the name. They are
applied in the order they are specified. If the element is still included after all filters
have been applied, it is inserted.

Each string can have the following value:
* `NONE`: Exclude all elements.
* `ALL`: Include all elements.
* `<regular expression>` or `+<regular expression`: Include elements that match the regular
  expression.
* `-<regular expression>`: Exclude elements that match the regular expression.

If the first string is an include regular expression, an implicit `NONE` is prepended, if
the first string is an exclude regular expression, an implicit `ALL` is prepended.

Some filters support filtering on other properties than the name. By default they only
filter on the name. To filter the other properties use a dictionary, where the key is the
name of the property, and the value is a string or list of strings with the filter.

### Linking to API reference

``` python
${api.link(<name>[, kind=<kind>][, lang=<language>][, text][, full_name])}
${api.link_<kind>(<name>[, lang=<language>][, text][, full_name])}

# Examples:
${api.link("MyNamespace::MyClass")}
${api.link("MyNamespace::MyClass", lang="c++")}
${api.link("com.tomtom.Class.Method", full_name=True)}
${api.link("MyNamespace::FreeFunction", text="FreeFunction")}
${api.link_class("MyNamespace::MyClass")}
${api.link_class("MyNamespace::MyClass", lang="c++")}
```

Insert a link to an API reference element. By default the short name of the element is used as the
text of the link.

  - `name`
    Fully qualified name of the element to insert.

  - `lang`
    Name of the programming language.

  - `kind`
    Kind of element to insert.

  - `text`
    Alternative text to use for the link.

  - `full_name`
    Use the fully qualified name of the referenced element.

By default a warning is shown if the element is unknown, or is not inserted in the same document
using an `insert_` method. There is a command-line option to throw an error instead.

When not specifying the language and kind, AsciiDoxy will try to find the element by name, and
deduce the kind and language. If there are multiple matching elements, an error is raised.

### Function or method overloads

In languages that support overloading functions, methods or other callables, the name alone is not
sufficient to select the correct element to link to or to insert. In this case the exact list of
types of the parameters can be provided to select the right element.

The list of parameter types should be specified in parentheses after the function name:

``` python
${api.link("MyFunction(int, std::string)")}
```

Empty parentheses indicate the function should accept no parameters:

``` python
${api.link("MyFunction()")}
```

If no parentheses are given, the parameters are ignored. If there are multiple overloads, AsciiDoxy
will not be able to pick one:

``` python
${api.link("MyFunction")}
```

### Including other AsciiDoc files

``` python
${api.include(<file_name>[, leveloffset=<offset>][, link_text=<text>][, link_prefix=<prefix>][, multi_page_link=<bool>])}

# Examples:
${api.include("component/reference.adoc")}
${api.include("/mount/data/reference.adoc", leveloffset="+3")}

# If you want your documentation to look nicely also as multi-page document, don't forget to pass
# link_text and optionally link_prefix arguments, e.g.:
${api.include("component/reference.adoc", link_text="Reference", link_prefix=". ")}

# If you want to embed a file in single-page, but not include a link in multi-page
${api.include("/component/reference.adoc", multi_page_link=False)}
```

Include another AsciiDoc file and process it using Mako as well. The normal AsciiDoc include
directives can be used as well, but will not process any Mako directives. With `--multi-page` option
the include method doesn’t embed the included document in its parent document but generates separate
output document instead. By default `multi_page_link` is `True`, so a link to the included document
is inserted in the parent document then.

Sometimes it is desirable to link from the parent document to the included document in a table, or
another place where the included document cannot be embedded. In this case, use
`api.cross_document_ref()` from the table and include the document where it should be embedded,
setting `multi_page_link` to `False`. The included document will still be processed using Mako, but
there will be no link.

  - `file_name`
    Relative or absolute path to the file to include.

  - `leveloffset`
    Offset for the headers in the included file from the top level of the current file. Defaults to
    +1.

### Cross-referencing sections in other AsciiDoc files

    ${api.cross_document_ref(<file_name>, anchor=<section-anchor>[, link_text=<text>])}

    # Examples:
    ${api.cross_document_ref("component/component_a.adoc", anchor="section-1")}
    ${api.cross_document_ref("component/component_a.adoc", anchor="section 1", link_text="Component A - Section 1")}

If you want your documentation to cross-reference sections between different AsciiDoc files and be
correctly rendered also in multi-page format you need to use this method to generate the reference.

### Setting default programming language

``` python
${api.language(<language>)}

# Examples:
${api.language("cpp")}
${api.language("c++")}
${api.language("java")}
${api.language(None)}
```

Set the default language for all following commands. Other languages will be ignored, unless
overridden with a `lang` argument. This setting also applies to all files included afterwards.

  - `language`
    Language to use as default, or `None` to reset.

### Starting namespace

``` python
${api.namespace(<namespace>)}

# Examples:
${api.namespace("com.tomtom.navkit2.")}
${api.namespace("tomtom::navkit2::")}
${api.namespace(None)}
```

Set a namespace prefix to start searching elements in. If the element is not found in this prefix,
it is treated as a fully qualified name.

Current support is not very smart yet. It only looks for the concatenation of namespace and name,
and if not found it searches again for just name. It does not understand namespace separators yet,
and will not try to find elements on other levels in the same namespace tree.

  - `namespace`
    Namespace prefix to search first, or `None` to reset.

## Development

AsciiDoxy is developed in python 3.6. For development it is recommended to set up a virtual
environment with all dependencies. Use the following commands to quickly set up the entire
environment:

``` bash
make virtualenv
```

Then enable the virtual environment to be able to run tests:

``` bash
. .venv/bin/activate
```

The make file defines several other helpful commands:

  - `make test`: Run unit tests using the current python version.

  - `make lint`: Check code style.

  - `make type-check`: Static analysis using type hints.

  - `make test-all`: Run all checks and tests on all available and supported python versions.

  - `make dist`: Create distribution packages in `dist/`.

  - `make release`: Upload packages created with `make dist` to PyPI.

  - `make docker`: Create a local build of the docker image.

Before creating a PR, you should run `make test-all` to run all tests, the linter and the type
checker. Packaging and specified requirements are verified as well by installing into a clean
virtual environment. Tests will be run on all available, and supported, python versions.

### Architecture overview

Modules:

  - `artifactory`: Downloads Doxygen XML archives from Artifactory and unpacks them.

  - `doxygen_xml`: Reads the Doxygen XML files and creates an internal representation that can be
    converted to AsciiDoc.

  - `model`: Internal representation of API reference elements.

  - `asciidoc`: Enriches an AsciiDoc file with API reference information.

  - `cli`: The command line interface.

### Adding programming language support

`DoxygenXmlParser` (in `doxygen_xml`) is the main entry point for loading the API reference from
Doxygen XML files. It uses an instance of `Language` to parse XML files with language specific
transformations. Too add support for an extra language:

  - Add a subclass of `Language`.

  - Register it in the constructor of `DoxygenXmlParser`.

  - If needed, add aliases in `safe_language_tag`.

### Adding methods for use in AsciiDoc files

The entry point for enriching an AsciiDoc file is `process_adoc()`. It treats the AsciiDoc input
file as a Mako template. Any [Mako syntax](https://docs.makotemplates.org/en/latest/syntax.html) can
be used in the AsciiDoc file. API enrichment methods are provided by passing an instance of `Api` to
the Mako processor. It is exposed in the document as `api`. Add methods to `Api` to provide more
functionality to document writers.

### Supporting more kinds of API reference elements

API reference fragments are also generated from Mako templates. These templates are in
`asciidoxy/templates` and are organised in separate directories per programming language. To add
support for a specific API reference element, add a Mako template with the name of the element in
the directory for the corresponding programming language. It will automatically be picked up when an
insert method is called. The special method `getattr` is used to provide the `insert_<kind>` and
`link_<kind>` methods.

### Coding style

For coding style we use [PEP8](https://www.python.org/dev/peps/pep-0008/), enforced by
[yapf](https://github.com/google/yapf). For docstrings we follow [Google
Style](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

### Test data

Where possible, Doxygen XML files for testing are generated from custom source code. This allows
checking compatibility with different Doxygen versions. Inside the `tests` directory there are
multiple directories for test data:

  - `adoc`: AsciiDoc input files for testing. Usually pairs of `<NAME>.input.adoc` and
    `<NAME>.expected.adoc`. The expected file contains what AsciiDoxy should output when processing
    the input file.

  - `data`: Handcrafted test data.

  - `source_code`: The source code from which Doxygen XML test data is generated.

  - `xml`: Doxygen XML test data generated from the source code.

The Doxygen XML data can be regenerated by running `tests/source_code/generate_xml.py`, and
providing the path to the version of Doxygen to use.

<div class="note">

A separate directory is created for each version of Doxygen. The tests will run on each directory.

</div>

The expectations for the tests in `test_templates.py` can be easily regenerated when templates have
been changed. Run `pytest --update-expected-results` to overwrite the current expectations with the
new output. Make sure to check the diff to see if there are no unexpected side effects!
