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
"""Models of API reference elements."""

from abc import ABC, abstractmethod
from typing import List, Optional


def json_repr(obj):
    data = {"__CLASS__": obj.__class__.__name__}
    data.update(vars(obj))
    return data


class ModelBase(ABC):
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            if not hasattr(self, name):
                raise TypeError(f"{self.__class__} has no attribute {name}.")
            setattr(self, name, value)


class ReferableElement(ModelBase):
    """Base class for all objects that can be referenced/linked to.

    Attributes:
        id:        Unique identifier, if available.
        name:      Short name of the element.
        full_name: Fully qualified name.
        language:  Language the element is written in.
        kind:      Kind of language element.
    """
    id: Optional[str] = None
    name: str = ""
    full_name: str = ""
    language: str
    kind: str = ""

    def __init__(self, language: str = "", **kwargs):
        super().__init__(**kwargs)
        self.language = language

    def __str__(self) -> str:
        text = (f"ReferableElement [\n id [{self.id}]\n  name [{self.name}]\n "
                f"full name[{self.full_name}]\n lang [{self.language}]\n kind [{self.kind}]")
        return text + "]"

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return ((self.id, self.name, self.full_name, self.language,
                 self.kind) == (other.id, other.name, other.full_name, other.language, other.kind))

    def __hash__(self):
        return hash((self.id, self.name, self.full_name, self.language, self.kind))


class TypeRefBase(ModelBase, ABC):
    """Base class for references to types.
    Attributes:
        id:        Unique identifier of the type.
        name:      Name of the type.
        language:  Language the type is written in.
        namespace: Namespace, or package, from which the type is referenced.
    """
    # doxygen based fields
    id: Optional[str] = None
    name: str
    # custom fields
    language: str
    namespace: Optional[str] = None

    def __init__(self, language: str = "", name: str = "", **kwargs):
        super().__init__(**kwargs)
        self.language = language
        self.name = name

    @abstractmethod
    def resolve(self, reference_target: ReferableElement) -> None:
        pass

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return ((self.id, self.name, self.language,
                 self.namespace) == (other.id, other.name, other.language, other.namespace))


class TypeRef(TypeRefBase):
    """Reference to a type.

    Representation of doxygen type linkedTextType

    Attributes:
        kind:      Kind of language element.
        prefix:    Qualifiers prefixing the type.
        suffix:    Qualifiers suffixing the type.
        nested:    List of nested types. None if no arguments, an empty list if zero arguments.
        args:      Arguments for function like types. None if no arguments, an empty list if zero
                       arguments.
        returns:   Return type in case of closure types.
    """

    # doxygen based fields
    kind: Optional[str] = None
    # custom fields
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    nested: Optional[List["TypeRef"]] = None
    args: Optional[List["Parameter"]] = None
    returns: Optional["TypeRef"] = None

    def __init__(self, language: str = "", name: str = "", **kwargs):
        super().__init__(language, name, **kwargs)

    def __str__(self) -> str:
        nested_str = ""
        if self.nested:
            nested_str = f"< {', '.join(str(t) for t in self.nested)} >"
        args_str = ""
        if self.args:
            args_str = f"({', '.join(f'{p.type} {p.name}' for p in self.args)})"
        return f"{self.prefix or ''}{self.name}{nested_str}{args_str}{self.suffix or ''}"

    def resolve(self, reference_target: ReferableElement) -> None:
        self.id = reference_target.id
        self.kind = reference_target.kind

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return (super().__eq__(other)
                and (self.kind, self.prefix, self.suffix, self.nested, self.args, self.returns)
                == (other.kind, other.prefix, other.suffix, other.nested, other.args,
                    other.returns))


class Parameter(ModelBase):
    """Parameter description.

    Representation of doxygen type paramType

    Attributes:
        type:          Reference to the type of the parameter.
        name:          Name used for the parameter.
        description:   Explanation of the parameter.
        default_value: Default value for the parameter.
        prefix:        Prefix for the parameter declaration.
    """

    # doxygen based fields
    type: Optional[TypeRef] = None
    name: str = ""
    description: str = ""
    default_value: Optional[str] = None
    prefix: Optional[str] = None

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return ((self.type, self.name, self.description, self.default_value,
                 self.prefix) == (other.type, other.name, other.description, other.default_value,
                                  other.prefix))


class ReturnValue(ModelBase):
    """Value returned from a member.

    Attributes:
        type:        Reference to the type of return value.
        description: Explanation of the return value.
    """

    type: Optional[TypeRef] = None
    description: str = ""

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return (self.type, self.description) == (other.type, other.description)


class ThrowsClause(ModelBase):
    """Potential exception thrown from a member.

    Attributes:
        type:        Reference to the type of the exception.
        description: Explanation of when the exception is thrown.

    """

    type: TypeRef
    description: str = ""

    def __init__(self, language: str = "", type: Optional[TypeRef] = None, **kwargs):
        super().__init__(**kwargs)
        self.type = type or TypeRef(language)

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return (self.type, self.description) == (other.type, other.description)


class EnumValue(ReferableElement):
    """Single value in an enum type.

    Attributes:
        initializer: Value assigned to the enum.
        brief:       Brief description of the enum value.
        description: Full description of the enum value.
    """

    # doxygen based fields
    initializer: str = ""
    brief: str = ""
    description: str = ""

    # custom fields
    kind: str = "enumvalue"

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return (super().__eq__(other) and (self.initializer, self.brief, self.description)
                == (other.initializer, other.brief, other.description))


class InnerTypeReference(TypeRefBase):
    """Representation of a reference to a type/class/member in the documentation.

    It can be used to reflect Doxygen::xml type refType.

    Attributes:
        referred_object: Element being referenced.
        prot:            Protection level of the inner type.
    """

    referred_object: Optional["Compound"] = None
    prot: str = ""

    def resolve(self, reference_target):
        self.referred_object = reference_target

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return (super().__eq__(other)
                and (self.referred_object, self.prot) == (other.referred_object, other.prot))


class Compound(ReferableElement):
    """Compound object. E.g. a class or enum.

    Representation of the doxygen type compound.

    Attributes:
        members:       List of members in the compound.
        inner_classes: References to inner types.
        brief:         Brief description of the compound.
        description:   Full description of the compound.
        enumvalues:    List of enum values contained in the compound.
        include:       Name of the include (file) required to use this compound.
        namespace:     Namespace, or package, the compound is contained in.
    """

    members: List["Compound"]
    inner_classes: List[InnerTypeReference]
    enumvalues: List[EnumValue]
    params: List[Parameter]
    exceptions: List[ThrowsClause]
    returns: Optional[ReturnValue] = None

    include: Optional[str] = None
    namespace: Optional[str] = None

    prot: str = ""
    definition: str = ""
    args: str = ""

    brief: str = ""
    description: str = ""

    static: bool = False
    const: bool = False
    deleted: bool = False
    default: bool = False
    constexpr: bool = False

    def __init__(self,
                 language: str = "",
                 *,
                 members: Optional[List["Compound"]] = None,
                 inner_classes: Optional[List[InnerTypeReference]] = None,
                 enumvalues: Optional[List[EnumValue]] = None,
                 params: Optional[List[Parameter]] = None,
                 exceptions: Optional[List[ThrowsClause]] = None,
                 **kwargs):
        super().__init__(language, **kwargs)
        self.members = members or []
        self.inner_classes = inner_classes or []
        self.enumvalues = enumvalues or []
        self.params = params or []
        self.exceptions = exceptions or []

    def __str__(self):
        return f"Compound [{super().__str__()}]"

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return (super().__eq__(other)
                and (self.members, self.inner_classes, self.enumvalues, self.params,
                     self.exceptions, self.returns, self.include, self.namespace, self.prot,
                     self.definition, self.args, self.brief, self.description, self.static,
                     self.const, self.deleted, self.default, self.constexpr)
                == (other.members, other.inner_classes, other.enumvalues, other.params,
                    other.exceptions, other.returns, other.include, other.namespace, other.prot,
                    other.definition, other.args, other.brief, other.description, other.static,
                    other.const, other.deleted, other.default, other.constexpr))

    def __hash__(self):
        return super().__hash__()
