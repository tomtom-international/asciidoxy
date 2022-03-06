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
"""Models of API reference elements."""

import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

if sys.version_info >= (3, 10):
    dataclass_options = {
        "slots": True,
        "kw_only": True,
    }
else:
    dataclass_options: Dict[str, Any] = {}


def json_repr(obj):
    data = {"__CLASS__": obj.__class__.__name__}
    data.update(asdict(obj))
    return data


@dataclass(**dataclass_options)
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
    language: str = ""
    kind: str = ""


@dataclass(**dataclass_options)
class TypeRef:
    """Reference to a type.

    Attributes:
        id:        Unique identifier of the type.
        name:      Name of the type.
        language:  Language the type is written in.
        namespace: Namespace, or package, from which the type is referenced.
        kind:      Kind of language element.
        prefix:    Qualifiers prefixing the type.
        suffix:    Qualifiers suffixing the type.
        nested:    List of nested types. None if no arguments, an empty list if zero arguments.
        args:      Arguments for function like types. None if no arguments, an empty list if zero
                       arguments.
        returns:   Return type in case of closure types.
        prot:      Protection level of the referenced type.
    """

    id: Optional[str] = None
    name: str = ""
    language: str = ""
    namespace: Optional[str] = None
    kind: Optional[str] = None

    prefix: Optional[str] = None
    suffix: Optional[str] = None
    nested: Optional[List["TypeRef"]] = None
    args: Optional[List["Parameter"]] = None
    returns: Optional["TypeRef"] = None
    prot: Optional[str] = None

    def resolve(self, reference_target: ReferableElement) -> None:
        self.id = reference_target.id
        self.kind = reference_target.kind


@dataclass(**dataclass_options)
class Parameter:
    """Parameter description.

    Representation of doxygen type paramType

    Attributes:
        type:          Reference to the type of the parameter.
        name:          Name used for the parameter.
        description:   Explanation of the parameter.
        default_value: Default value for the parameter.
        prefix:        Prefix for the parameter declaration.
        kind:          The kind of parameter.
    """

    type: Optional[TypeRef] = None
    name: str = ""
    description: str = ""
    default_value: Optional[str] = None
    prefix: Optional[str] = None
    kind: str = "param"


@dataclass(**dataclass_options)
class ReturnValue:
    """Value returned from a member.

    Attributes:
        type:        Reference to the type of return value.
        description: Explanation of the return value.
    """

    type: Optional[TypeRef] = None
    description: str = ""


@dataclass(**dataclass_options)
class ThrowsClause:
    """Potential exception thrown from a member.

    Attributes:
        type:        Reference to the type of the exception.
        description: Explanation of when the exception is thrown.

    """

    type: TypeRef = field(default_factory=TypeRef)
    description: str = ""


@dataclass(**dataclass_options)
class Compound(ReferableElement):
    """Compound object. E.g. a class or enum.

    Representation of the doxygen type compound.

    Attributes:
        members:       List of members in the compound.
        params:        List of parameters.
        exceptions:    List of exceptions that can be thrown.
        returns:       Return value.
        include:       Name of the include (file) required to use this compound.
        namespace:     Namespace, or package, the compound is contained in.
        prot:          Protection or visibility level.
        definition:    Full definition in source code.
        args:          All arguments as in source code.
        initializer:   Initial value assignment.
        brief:         Brief description of the compound.
        description:   Full description of the compound.
        sections:      Extra documentation sections with special meanings.
        static:        True if this is marked as static.
        const:         True if this is marked as const.
        deleted:       True if this is marked as deleted.
        default:       True if this is marked as default.
        constexpr:     True if this is marked as constexpr.
    """

    members: List["Compound"] = field(default_factory=list)
    params: List[Parameter] = field(default_factory=list)
    exceptions: List[ThrowsClause] = field(default_factory=list)
    returns: Optional[ReturnValue] = None

    include: Optional[str] = None
    namespace: Optional[str] = None

    prot: str = ""
    definition: str = ""
    args: str = ""
    initializer: str = ""

    brief: str = ""
    description: str = ""
    sections: Dict[str, str] = field(default_factory=dict)

    static: bool = False
    const: bool = False
    deleted: bool = False
    default: bool = False
    constexpr: bool = False
