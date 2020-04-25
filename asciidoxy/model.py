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


class ReferableElement:
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

    def __init__(self, language: str):
        self.language = language

    def __str__(self) -> str:
        text = (f"ReferableElement [\n id [{self.id}]\n  name [{self.name}]\n "
                "full name[{self.full_name}]\n lang [{self.language}]\n kind [{self.kind}]")
        return text + "]"


class TypeRefBase(ABC):
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

    def __init__(self, language: str, name: str = ""):
        self.language = language
        self.name = name

    @abstractmethod
    def resolve(self, reference_target: ReferableElement) -> None:
        pass


class TypeRef(TypeRefBase):
    """Reference to a type.

    Representation of doxygen type linkedTextType

    Attributes:
        kind:      Kind of language element.
        prefix:    Qualifiers prefixing the type.
        suffix:    Qualifiers suffixing the type.
        nested:    List of nested types.
    """

    # doxygen based fields
    kind: Optional[str] = None
    # custom fields
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    nested: List["TypeRef"]

    def __init__(self, language: str, name: str = ""):
        super().__init__(language, name)
        self.name = name
        self.language = language
        self.nested = []

    def __str__(self) -> str:
        nested_str = ""
        if self.nested:
            nested_str = f"< {', '.join(str(t) for t in self.nested)} >"
        return f"{self.prefix or ''}{self.name}{nested_str}{self.suffix or ''}"

    def resolve(self, reference_target: ReferableElement) -> None:
        self.id = reference_target.id
        self.kind = reference_target.kind


class Parameter:
    """Parameter description.

    Representation of doxygen type paramType

    Attributes:
        type:        Reference to the type of the parameter.
        name:        Name used for the parameter.
        description: Explanation of the parameter.
    """

    # doxygen based fields
    type: Optional[TypeRef] = None
    name: str = ""
    description: str = ""


class ReturnValue:
    """Value returned from a member.

    Attributes:
        type:        Reference to the type of return value.
        description: Explanation of the return value.
    """

    type: Optional[TypeRef] = None
    description: str = ""


class ThrowsClause:
    """Potential exception thrown from a member.

    Attributes:
        type:        Reference to the type of the exception.
        description: Explanation of when the exception is thrown.

    """

    type: TypeRef
    description: str = ""

    def __init__(self, language: str):
        self.type = TypeRef(language)


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


class Member(ReferableElement):
    """Member of a compound object.

    Representation of the doxygen type memberDef.

    Attributes:
        definition:  Full definition of the member in source code.
        args:        The arguments as defined in the source code.
        params:      List of parameters.
        exceptions:  List of exceptions that can be thrown.
        brief:       Brief description of the member.
        description: Full description of the member.
        prot:        Protection level of the member.
        returns:     The return value of the member.
        enumvalues:  List of enum values contained in the member.
        static:      True if this is a static member.
        include:     Name of the include (file) required to use this member.
        namespace:   Namespace, or scope, the member is contained in.
    """

    definition: str = ""
    args: str = ""
    params: List[Parameter]
    exceptions: List[ThrowsClause]
    brief: str = ""
    description: str = ""
    prot: str = ""
    returns: Optional[ReturnValue] = None
    enumvalues: List[EnumValue]
    static: bool = False
    include: Optional[str] = None
    namespace: Optional[str] = None

    def __init__(self, language: str):
        super().__init__(language)
        self.params = []
        self.exceptions = []
        self.enumvalues = []

    def __str__(self):
        return f"Member [{super().__str__()}]"


class InnerTypeReference(TypeRefBase):
    """Representation of a reference to a type/class/member in the documentation.

    It can be used to reflect Doxygen::xml type refType.

    Attributes:
        referred_object: Element being referenced.
    """

    referred_object: Optional["Compound"] = None

    def resolve(self, reference_target):
        self.referred_object = reference_target


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

    members: List[Member]
    inner_classes: List[InnerTypeReference]
    brief: str = ""
    description: str = ""
    enumvalues: List[EnumValue]
    include: Optional[str] = None
    namespace: Optional[str] = None

    def __init__(self, language: str):
        super().__init__(language)
        self.members = []
        self.inner_classes = []
        self.enumvalues = []

    def __str__(self):
        return f"Compound [{super().__str__()}]"
