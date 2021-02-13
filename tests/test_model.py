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
Tests for the `asciidoxy.model` module.
"""

from asciidoxy.model import (Compound, EnumValue, Parameter, ReferableElement, ReturnValue,
                             ThrowsClause, TypeRef, InnerTypeReference)


def test_minimal_constructed_repr():
    assert repr(TypeRef("lang"))
    assert repr(Parameter())
    assert repr(ReturnValue())
    assert repr(ThrowsClause("lang"))
    assert repr(EnumValue("lang"))
    assert repr(Compound("lang"))
    assert repr(InnerTypeReference("lang"))


def test_type_ref_to_str():
    assert str(TypeRef("cpp")) == ""
    assert str(TypeRef("cpp", "Type")) == "Type"

    type_ref = TypeRef("cpp", "Type")
    type_ref.id = "12345"
    assert str(type_ref) == "Type"

    type_ref.kind = "class"
    assert str(type_ref) == "Type"

    type_ref.prefix = "const "
    assert str(type_ref) == "const Type"

    type_ref.suffix = " &"
    assert str(type_ref) == "const Type &"

    nested_type_1 = TypeRef("cpp", "Nested1")
    type_ref.nested = [nested_type_1]
    assert str(type_ref) == "const Type< Nested1 > &"

    nested_type_2 = TypeRef("cpp", "Nested2")
    nested_type_2.prefix = "const "
    nested_type_2.suffix = "*"
    type_ref.nested.append(nested_type_2)
    assert str(type_ref) == "const Type< Nested1, const Nested2* > &"

    nested_type_2.nested = [nested_type_1]
    assert str(type_ref) == "const Type< Nested1, const Nested2< Nested1 >* > &"


def test_referable_element__init__default():
    element = ReferableElement()
    assert element.id is None
    assert element.name == ""
    assert element.full_name == ""
    assert element.language == ""
    assert element.kind == ""


def test_referable_element__init__positional():
    element = ReferableElement("lang")
    assert element.id is None
    assert element.name == ""
    assert element.full_name == ""
    assert element.language == "lang"
    assert element.kind == ""


def test_referable_element__init__keywords():
    element = ReferableElement(language="lang",
                               id="id",
                               name="name",
                               full_name="full_name",
                               kind="kind")
    assert element.id == "id"
    assert element.name == "name"
    assert element.full_name == "full_name"
    assert element.language == "lang"
    assert element.kind == "kind"


def test_referable_element__eq__none():
    element = ReferableElement()
    assert not element == None  # noqa: E711
    assert not None == element  # noqa: E711

    assert element != None  # noqa: E711
    assert None != element  # noqa: E711


def test_referable_element__eq__default():
    first = ReferableElement()
    second = ReferableElement()

    assert first == second
    assert second == first


def test_referable_element__eq__minimal():
    first = ReferableElement("lang")
    second = ReferableElement("lang")

    assert first == second
    assert second == first


def test_referable_element__eq__full():
    first = ReferableElement(language="lang",
                             id="id",
                             name="name",
                             full_name="full_name",
                             kind="kind")
    second = ReferableElement(language="lang",
                              id="id",
                              name="name",
                              full_name="full_name",
                              kind="kind")

    assert first == second
    assert second == first

    second.id = "other"
    assert first != second
    assert second != first
    second.id = "id"

    second.name = "other"
    assert first != second
    assert second != first
    second.name = "name"

    second.full_name = "other"
    assert first != second
    assert second != first
    second.full_name = "full_name"

    second.kind = "other"
    assert first != second
    assert second != first


def test_typeref__init__default():
    ref = TypeRef()
    assert ref.id is None
    assert ref.name == ""
    assert ref.language == ""
    assert ref.namespace is None
    assert ref.kind is None
    assert ref.prefix is None
    assert ref.suffix is None
    assert ref.nested is None
    assert ref.args is None
    assert ref.returns is None


def test_typeref__init__positional():
    ref = TypeRef("lang", "name")
    assert ref.id is None
    assert ref.name == "name"
    assert ref.language == "lang"
    assert ref.namespace is None
    assert ref.kind is None
    assert ref.prefix is None
    assert ref.suffix is None
    assert ref.nested is None
    assert ref.args is None
    assert ref.returns is None


def test_typeref__init__keywords():
    ref = TypeRef(language="lang",
                  name="name",
                  id="id",
                  namespace="namespace",
                  kind="kind",
                  prefix="prefix",
                  suffix="suffix",
                  nested=[TypeRef(name="nested")],
                  args=[Parameter(name="parameter")],
                  returns=TypeRef(name="returns"))
    assert ref.id == "id"
    assert ref.name == "name"
    assert ref.language == "lang"
    assert ref.namespace == "namespace"
    assert ref.kind == "kind"
    assert ref.prefix == "prefix"
    assert ref.suffix == "suffix"

    assert len(ref.nested) == 1
    assert ref.nested[0].name == "nested"

    assert len(ref.args) == 1
    assert ref.args[0].name == "parameter"

    assert ref.returns is not None
    assert ref.returns.name == "returns"


def test_typeref__eq__none():
    ref = TypeRef()
    assert not ref == None  # noqa: E711
    assert not None == ref  # noqa: E711

    assert ref != None  # noqa: E711
    assert None != ref  # noqa: E711


def test_typeref__eq__default():
    first = TypeRef()
    second = TypeRef()

    assert first == second
    assert second == first


def test_typeref__eq__minimal():
    first = TypeRef("lang", "name")
    second = TypeRef("lang", "name")

    assert first == second
    assert second == first


def test_typeref__eq__full():
    first = TypeRef(language="lang",
                    name="name",
                    id="id",
                    namespace="namespace",
                    kind="kind",
                    prefix="prefix",
                    suffix="suffix",
                    nested=[TypeRef(name="nested")],
                    args=[Parameter(name="parameter")],
                    returns=TypeRef(name="returns"))
    second = TypeRef(language="lang",
                     name="name",
                     id="id",
                     namespace="namespace",
                     kind="kind",
                     prefix="prefix",
                     suffix="suffix",
                     nested=[TypeRef(name="nested")],
                     args=[Parameter(name="parameter")],
                     returns=TypeRef(name="returns"))

    assert first == second
    assert second == first

    for attr_name in ("language", "name", "id", "namespace", "kind", "prefix", "suffix"):
        setattr(second, attr_name, "other")
        assert first != second
        assert second != first
        setattr(second, attr_name, getattr(first, attr_name))

    second.nested[0].name = "other"
    assert first != second
    assert second != first
    second.nested[0].name = first.nested[0].name

    second.args[0].name = "other"
    assert first != second
    assert second != first
    second.args[0].name = first.args[0].name

    second.returns.name = "other"
    assert first != second
    assert second != first
    second.returns.name = first.returns.name


def test_typeref__resolve():
    ref = TypeRef(name="name")
    assert ref.id is None
    assert ref.kind is None

    ref.resolve(Compound(id="id", kind="kind"))
    assert ref.id == "id"
    assert ref.kind == "kind"


def test_parameter__init__default():
    param = Parameter()
    assert param.type is None
    assert param.name == ""
    assert param.description == ""
    assert param.default_value is None
    assert param.prefix is None


def test_parameter__init__keywords():
    param = Parameter(type=TypeRef(name="type"),
                      name="name",
                      description="description",
                      default_value="default_value",
                      prefix="prefix")
    assert param.type is not None
    assert param.type.name == "type"
    assert param.name == "name"
    assert param.description == "description"
    assert param.default_value == "default_value"
    assert param.prefix == "prefix"


def test_parameter__eq__none():
    param = Parameter()
    assert not param == None  # noqa: E711
    assert not None == param  # noqa: E711

    assert param != None  # noqa: E711
    assert None != param  # noqa: E711


def test_parameter__eq__minimal():
    first = Parameter()
    second = Parameter()

    assert first == second
    assert second == first


def test_parameter__eq__full():
    first = Parameter(type=TypeRef(name="type"),
                      name="name",
                      description="description",
                      default_value="default_value",
                      prefix="prefix")
    second = Parameter(type=TypeRef(name="type"),
                       name="name",
                       description="description",
                       default_value="default_value",
                       prefix="prefix")

    assert first == second
    assert second == first

    for attr_name in ("name", "description", "default_value", "prefix"):
        setattr(second, attr_name, "other")
        assert first != second
        assert second != first
        setattr(second, attr_name, getattr(first, attr_name))

    second.type.name = "other"
    assert first != second
    assert second != first
    second.type.name = first.type.name


def test_return_value__init__default():
    return_value = ReturnValue()
    assert return_value.type is None
    assert return_value.description == ""


def test_return_value__init__keywords():
    return_value = ReturnValue(type=TypeRef(name="type"), description="description")
    assert return_value.type is not None
    assert return_value.type.name == "type"
    assert return_value.description == "description"


def test_return_value__eq__none():
    return_value = ReturnValue()
    assert not return_value == None  # noqa: E711
    assert not None == return_value  # noqa: E711

    assert return_value != None  # noqa: E711
    assert None != return_value  # noqa: E711


def test_return_value__eq__minimal():
    first = ReturnValue()
    second = ReturnValue()

    assert first == second
    assert second == first


def test_return_value__eq__full():
    first = ReturnValue(type=TypeRef(name="type"), description="description")
    second = ReturnValue(type=TypeRef(name="type"), description="description")

    assert first == second
    assert second == first

    second.type.name = "other"
    assert first != second
    assert second != first
    second.type.name = first.type.name

    second.description = "other"
    assert first != second
    assert second != first
    second.description = first.description


def test_throws_clause__init__default():
    throws_clause = ThrowsClause()
    assert throws_clause.type is not None
    assert throws_clause.type.language == ""
    assert throws_clause.description == ""


def test_throws_clause__init__language_only():
    throws_clause = ThrowsClause("lang")
    assert throws_clause.type is not None
    assert throws_clause.type.language == "lang"
    assert throws_clause.description == ""


def test_throws_clause__init__typeref():
    throws_clause = ThrowsClause(type=TypeRef(name="type"), description="description")
    assert throws_clause.type is not None
    assert throws_clause.type.name == "type"
    assert throws_clause.description == "description"


def test_throws_clause__eq__none():
    throws_clause = ThrowsClause()
    assert not throws_clause == None  # noqa: E711
    assert not None == throws_clause  # noqa: E711

    assert throws_clause != None  # noqa: E711
    assert None != throws_clause  # noqa: E711


def test_throws_clause__eq__default():
    first = ThrowsClause()
    second = ThrowsClause()

    assert first == second
    assert second == first


def test_throws_clause__eq__full():
    first = ThrowsClause(type=TypeRef(name="type"), description="description")
    second = ThrowsClause(type=TypeRef(name="type"), description="description")

    assert first == second
    assert second == first

    second.type.name = "other"
    assert first != second
    assert second != first
    second.type.name = first.type.name

    second.description = "other"
    assert first != second
    assert second != first
    second.description = first.description


def test_enum_value__init__default():
    enum_value = EnumValue()
    assert enum_value.id is None
    assert enum_value.name == ""
    assert enum_value.full_name == ""
    assert enum_value.language == ""
    assert enum_value.kind == "enumvalue"
    assert enum_value.initializer == ""
    assert enum_value.brief == ""
    assert enum_value.description == ""


def test_enum_value__init__full():
    enum_value = EnumValue(id="id",
                           name="name",
                           full_name="full_name",
                           language="lang",
                           initializer="initializer",
                           brief="brief",
                           description="description")
    assert enum_value.id == "id"
    assert enum_value.name == "name"
    assert enum_value.full_name == "full_name"
    assert enum_value.language == "lang"
    assert enum_value.kind == "enumvalue"
    assert enum_value.initializer == "initializer"
    assert enum_value.brief == "brief"
    assert enum_value.description == "description"


def test_enum_value__eq__none():
    enum_value = EnumValue()
    assert not enum_value == None  # noqa: E711
    assert not None == enum_value  # noqa: E711

    assert enum_value != None  # noqa: E711
    assert None != enum_value  # noqa: E711


def test_enum_value__eq__default():
    first = EnumValue()
    second = EnumValue()

    assert first == second
    assert second == first


def test_enum_value__eq__full():
    first = EnumValue(id="id",
                      name="name",
                      full_name="full_name",
                      language="lang",
                      initializer="initializer",
                      brief="brief",
                      description="description")
    second = EnumValue(id="id",
                       name="name",
                       full_name="full_name",
                       language="lang",
                       initializer="initializer",
                       brief="brief",
                       description="description")

    assert first == second
    assert second == first

    for attr_name in ("id", "name", "full_name", "language", "initializer", "brief", "description"):
        setattr(second, attr_name, "other")
        assert first != second
        assert second != first
        setattr(second, attr_name, getattr(first, attr_name))


def test_inner_type_reference__init__default():
    ref = InnerTypeReference()
    assert ref.id is None
    assert ref.name == ""
    assert ref.language == ""
    assert ref.namespace is None
    assert ref.referred_object is None
    assert ref.prot == ""


def test_inner_type_reference__init__positional():
    ref = InnerTypeReference("lang", "name")
    assert ref.id is None
    assert ref.name == "name"
    assert ref.language == "lang"
    assert ref.namespace is None
    assert ref.referred_object is None
    assert ref.prot == ""


def test_inner_type_reference__init__keyword():
    ref = InnerTypeReference(id="id",
                             language="lang",
                             name="name",
                             namespace="namespace",
                             referred_object=Compound("lang", name="inner_type"),
                             prot="prot")
    assert ref.id == "id"
    assert ref.name == "name"
    assert ref.language == "lang"
    assert ref.namespace == "namespace"
    assert ref.referred_object is not None
    assert ref.referred_object.name == "inner_type"
    assert ref.prot == "prot"


def test_inner_type_reference__eq__none():
    inner_type_reference = InnerTypeReference()
    assert not inner_type_reference == None  # noqa: E711
    assert not None == inner_type_reference  # noqa: E711

    assert inner_type_reference != None  # noqa: E711
    assert None != inner_type_reference  # noqa: E711


def test_inner_type_reference__eq__default():
    first = InnerTypeReference()
    second = InnerTypeReference()

    assert first == second
    assert second == first


def test_inner_type_reference__eq__full():
    first = InnerTypeReference(id="id",
                               language="lang",
                               name="name",
                               namespace="namespace",
                               referred_object=Compound("lang", name="inner_type"),
                               prot="prot")
    second = InnerTypeReference(id="id",
                                language="lang",
                                name="name",
                                namespace="namespace",
                                referred_object=Compound("lang", name="inner_type"),
                                prot="prot")

    assert first == second
    assert second == first

    for attr_name in ("id", "name", "language", "namespace", "prot"):
        setattr(second, attr_name, "other")
        assert first != second
        assert second != first
        setattr(second, attr_name, getattr(first, attr_name))

    second.referred_object.name = "other"
    assert first != second
    assert second != first
    second.referred_object.name = first.referred_object.name


def test_inner_type_reference__resolve():
    ref = InnerTypeReference()
    ref.resolve(Compound(name="inner_type"))
    assert ref.referred_object is not None
    assert ref.referred_object.name == "inner_type"


def test_compound__init__default():
    compound = Compound()
    assert compound.id is None
    assert compound.name == ""
    assert compound.full_name == ""
    assert compound.language == ""
    assert compound.kind == ""

    assert compound.members == []
    assert compound.inner_classes == []
    assert compound.enumvalues == []
    assert compound.params == []
    assert compound.exceptions == []
    assert compound.returns is None

    assert compound.include is None
    assert compound.namespace is None

    assert compound.prot == ""
    assert compound.definition == ""
    assert compound.args == ""

    assert compound.brief == ""
    assert compound.description == ""

    assert compound.static is False
    assert compound.const is False
    assert compound.deleted is False
    assert compound.default is False
    assert compound.constexpr is False


def test_compound__init__positional():
    compound = Compound("lang")
    assert compound.id is None
    assert compound.name == ""
    assert compound.full_name == ""
    assert compound.language == "lang"
    assert compound.kind == ""

    assert compound.members == []
    assert compound.inner_classes == []
    assert compound.enumvalues == []
    assert compound.params == []
    assert compound.exceptions == []
    assert compound.returns is None

    assert compound.include is None
    assert compound.namespace is None

    assert compound.prot == ""
    assert compound.definition == ""
    assert compound.args == ""

    assert compound.brief == ""
    assert compound.description == ""

    assert compound.static is False
    assert compound.const is False
    assert compound.deleted is False
    assert compound.default is False
    assert compound.constexpr is False


def test_compound__init__keyword():
    compound = Compound(id="id",
                        name="name",
                        full_name="full_name",
                        language="lang",
                        kind="kind",
                        members=[Compound(name="member_name")],
                        inner_classes=[InnerTypeReference(name="inner_type_name")],
                        enumvalues=[EnumValue(name="enum_value_name")],
                        params=[Parameter(name="parameter")],
                        exceptions=[ThrowsClause(description="exception")],
                        returns=ReturnValue(description="returns"),
                        include="include",
                        namespace="namespace",
                        prot="prot",
                        definition="definition",
                        args="args",
                        brief="brief",
                        description="description",
                        static=True,
                        const=True,
                        deleted=True,
                        default=True,
                        constexpr=True)

    assert compound.id == "id"
    assert compound.name == "name"
    assert compound.full_name == "full_name"
    assert compound.language == "lang"
    assert compound.kind == "kind"

    assert len(compound.members) == 1
    assert compound.members[0].name == "member_name"
    assert len(compound.inner_classes) == 1
    assert compound.inner_classes[0].name == "inner_type_name"
    assert len(compound.enumvalues) == 1
    assert compound.enumvalues[0].name == "enum_value_name"
    assert len(compound.params) == 1
    assert compound.params[0].name == "parameter"
    assert len(compound.exceptions) == 1
    assert compound.exceptions[0].description == "exception"
    assert compound.returns is not None
    assert compound.returns.description == "returns"

    assert compound.include == "include"
    assert compound.namespace == "namespace"

    assert compound.prot == "prot"
    assert compound.definition == "definition"
    assert compound.args == "args"

    assert compound.brief == "brief"
    assert compound.description == "description"

    assert compound.static is True
    assert compound.const is True
    assert compound.deleted is True
    assert compound.default is True
    assert compound.constexpr is True


def test_compound__eq__none():
    compound = Compound()
    assert not compound == None  # noqa: E711
    assert not None == compound  # noqa: E711

    assert compound != None  # noqa: E711
    assert None != compound  # noqa: E711


def test_compound__eq__default():
    first = Compound()
    second = Compound()

    assert first == second
    assert second == first


def test_compound__eq__minimal():
    first = Compound("lang")
    second = Compound("lang")

    assert first == second
    assert second == first


def test_compound__eq__full():
    first = Compound(id="id",
                     name="name",
                     full_name="full_name",
                     language="lang",
                     kind="kind",
                     members=[Compound(name="member_name")],
                     inner_classes=[InnerTypeReference(name="inner_type_name")],
                     enumvalues=[EnumValue(name="enum_value_name")],
                     params=[Parameter(name="parameter")],
                     exceptions=[ThrowsClause(description="exception")],
                     returns=ReturnValue(description="returns"),
                     include="include",
                     namespace="namespace",
                     prot="prot",
                     definition="definition",
                     args="args",
                     brief="brief",
                     description="description",
                     static=True,
                     const=True,
                     deleted=True,
                     default=True,
                     constexpr=True)
    second = Compound(id="id",
                      name="name",
                      full_name="full_name",
                      language="lang",
                      kind="kind",
                      members=[Compound(name="member_name")],
                      inner_classes=[InnerTypeReference(name="inner_type_name")],
                      enumvalues=[EnumValue(name="enum_value_name")],
                      params=[Parameter(name="parameter")],
                      exceptions=[ThrowsClause(description="exception")],
                      returns=ReturnValue(description="returns"),
                      include="include",
                      namespace="namespace",
                      prot="prot",
                      definition="definition",
                      args="args",
                      brief="brief",
                      description="description",
                      static=True,
                      const=True,
                      deleted=True,
                      default=True,
                      constexpr=True)

    assert first == second
    assert second == first

    for attr_name in ("id", "name", "full_name", "language", "kind", "include", "namespace", "prot",
                      "definition", "args", "brief", "description"):
        setattr(second, attr_name, "other")
        assert first != second
        assert second != first
        setattr(second, attr_name, getattr(first, attr_name))

    for attr_name in ("static", "const", "deleted", "default", "constexpr"):
        setattr(second, attr_name, False)
        assert first != second
        assert second != first
        setattr(second, attr_name, getattr(first, attr_name))

    second.members[0].name = "other"
    assert first != second
    assert second != first
    second.members[0].name = first.members[0].name

    second.inner_classes[0].name = "other"
    assert first != second
    assert second != first
    second.inner_classes[0].name = first.inner_classes[0].name

    second.enumvalues[0].name = "other"
    assert first != second
    assert second != first
    second.enumvalues[0].name = first.enumvalues[0].name

    second.params[0].name = "other"
    assert first != second
    assert second != first
    second.params[0].name = first.params[0].name

    second.exceptions[0].description = "other"
    assert first != second
    assert second != first
    second.exceptions[0].description = first.exceptions[0].description

    second.returns.description = "other"
    assert first != second
    assert second != first
    second.returns.description = first.returns.description
