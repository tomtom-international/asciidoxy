## Copyright (C) 2019-2021, TomTom (http://tomtom.com).
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

################################################################################ Helper includes ##
<%!
from asciidoxy.templates.swift.helpers import SwiftTemplateHelper
from html import escape
%>
<%
helper = SwiftTemplateHelper(api, element, insert_filter)
%>

[[${element.id},${element.name}]]
${api.inserted(element)}
[source,swift,subs="-specialchars,macros+"]
----
${escape(helper.method_signature(element))}
----

${element.brief}

${element.description}

% if element.params or element.exceptions or element.returns or element.precondition or element.postcondition:
[cols='h,5a']
|===
% if element.precondition:
| Precondition
| ${element.precondition}

% endif
% if element.postcondition:
| Postcondition
| ${element.postcondition}

% endif
% if element.params:
| Parameters
|
% for param in element.params:
`${helper.parameter(param)}`::
${param.description}

% endfor
% endif
% if element.returns and element.returns.type.name != "void":
| Returns
|
`${helper.print_ref(element.returns.type)}`::
${element.returns.description}

% endif
% if element.exceptions:
| Throws
|
% for exception in element.exceptions:
`${exception.type.name}`::
${exception.description}

% endfor
%endif
|===
% endif
