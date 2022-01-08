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
from asciidoxy.generator.templates.helpers import has, has_any, h1, tc
from asciidoxy.generator.templates.python.helpers import params, PythonTemplateHelper
from html import escape
%>
<%
helper = PythonTemplateHelper(api)
%>
[#${element.id},reftext='${element.full_name}']
${h1(leveloffset, element.name)}
${api.inserted(element)}

[source,python,subs="-specialchars,macros+"]
----
${escape(helper.method_signature(element))}
----

${element.brief}

${element.description}

% if has_any(params(element), insert_filter.exceptions(element), element.sections) or element.returns:
[cols='h,5a']
|===
% for section_title, section_text in element.sections.items():
| ${section_title}
| ${section_text | tc}

% endfor
% if has(params(element)):
| Parameters
|
% for param in params(element):
`${helper.parameter(param)}`::
${param.description | tc}
% if param.default_value:
+
*Default value*: `${param.default_value | tc}`
% endif

% endfor
% endif
% if element.returns and element.returns.type.name != "None":
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
