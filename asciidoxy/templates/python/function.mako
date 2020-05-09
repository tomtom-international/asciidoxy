## Copyright (C) 2019-2020, TomTom (http://tomtom.com).
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
<%!
from asciidoxy.templates.helpers import (link_from_ref, has)
from asciidoxy.templates.python.helpers import (type_and_name, argument_list, params)
%>

= [[${element.id},${element.name}]]
${api_context.insert(element)}

[source,python,subs="-specialchars,macros+"]
----
${"@staticmethod\n" if element.static else ""}\
def ${element.name}${argument_list(element.params, api_context)} \
-> ${link_from_ref(element.returns.type, api_context) if element.returns else "None"}
----

${element.brief}

${element.description}

% if has(params(element)) or has(insert_filter.exceptions(element)) or element.returns:
[cols='h,5a']
|===
% if has(params(element)):
| Parameters
|
% for param in params(element):
`${type_and_name(param, api_context)}`::
${param.description}

% endfor
% endif
% if element.returns and element.returns.type.name != "None":
| Returns
|
`${link_from_ref(element.returns.type, api_context)}`::
${element.returns.description}

% endif
% if has(insert_filter.exceptions(element)):
| Throws
|
% for exception in insert_filter.exceptions(element):
`${exception.type.name}`::
${exception.description}

% endfor
%endif
|===
% endif
