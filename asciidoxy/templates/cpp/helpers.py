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
"""Helper functions for C++ templates."""


def public_static_methods(element):
    return (m for m in element.members
            if (m.kind == "function" and m.returns and not m.name.startswith("operator")
                and m.prot == "public" and m.static))


def public_methods(element):
    return (m for m in element.members
            if (m.kind == "function" and m.returns and not m.name.startswith("operator")
                and m.prot == "public" and not m.static))


def public_constructors(element):
    constructor_name = element.name
    return (m for m in element.members
            if m.kind == "function" and m.name == constructor_name and m.prot == "public")


def public_simple_enclosed_types(element):
    return (m for m in element.members
            if m.prot in ("public", "protected", None) and m.kind in ["enum", "typedef"])


def public_complex_enclosed_types(element):
    return (m.referred_object for m in element.inner_classes if m.referred_object is not None)


def public_variables(element):
    return (m for m in element.members if m.kind == "variable" and m.prot == "public")
