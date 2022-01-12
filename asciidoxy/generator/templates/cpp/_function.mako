## Copyright (C) 2019, TomTom (http://tomtom.com).
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
from asciidoxy.generator.templates.helpers import has, has_any, tc, param_filter
from asciidoxy.generator.templates.cpp.helpers import CppTemplateHelper
%>
<%
helper = CppTemplateHelper(api)
%>
${element.brief}

${element.description}

% if has_any(element.params, insert_filter.exceptions(element), element.sections) or element.returns:
[cols='h,5a']
|===
% for section_title, section_text in element.sections.items():
| ${section_title}
| ${section_text | tc}

% endfor
% if has(param_filter(element.params)):
| Parameters
|
% for param in param_filter(element.params):
`${helper.parameter(param)}`::
${param.description | tc}
% if param.default_value:
+
*Default value*: `${param.default_value | tc}`
% endif

% endfor
% endif
% if has(param_filter(element.params, kind="tparam")):
| Template Parameters
|
% for param in param_filter(element.params, kind="tparam"):
`${helper.parameter(param)}`::
${param.description | tc}
% if param.default_value:
+
*Default value*: `${param.default_value | tc}`
% endif

% endfor
% endif
% if element.returns and element.returns.type.name != "void":
| Returns
|
`${helper.print_ref(element.returns.type)}`::
${element.returns.description | tc}

% endif
% if has(insert_filter.exceptions(element)):
| Throws
|
% for exception in insert_filter.exceptions(element):
`${helper.print_ref(exception.type)}`::
${exception.description | tc}

% endfor
%endif
|===
% endif
