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
from asciidoxy.templates.helpers import has, has_any
from asciidoxy.templates.cpp.helpers import CppTemplateHelper
%>
<%
helper = CppTemplateHelper(api)
%>
${element.brief}

${element.description}

% if has_any(element.params, insert_filter.exceptions(element)) or element.returns:
[cols='h,5a']
|===
% if has(element.params):
| Parameters
|
% for param in element.params:
`${helper.parameter(param)}`::
${param.description}
% if param.default_value:
+
*Default value*: `${param.default_value}`
% endif

% endfor
% endif
% if element.returns and element.returns.type.name != "void":
| Returns
|
`${helper.print_ref(element.returns.type)}`::
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
