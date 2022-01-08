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

################################################################################ Helper includes ##
<%!
from asciidoxy.generator.templates.helpers import has, has_any, h1, h2, tc, param_filter
from asciidoxy.generator.templates.cpp.helpers import CppTemplateHelper
from html import escape
from itertools import chain
%>
<%
helper = CppTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
[#${element.id},reftext='${element.full_name}']
${h1(leveloffset, element.name)}
${api.inserted(element)}

[source,cpp,subs="-specialchars,macros+"]
----
% if element.include:
#include &lt;${element.include}&gt;

% endif
% if has(param_filter(element.params, kind="tparam")):
${helper.type_list(element.params, kind="tparam", start="template<", end=">") | escape}
%endif
${"struct" if element.kind == "struct" else "class"} ${element.full_name}
----
${element.brief}

${element.description}

<%
for prot in ("public", "protected", "private"):
    if has_any(param_filter(element.params, kind="tparam"),
               helper.simple_enclosed_types(prot=prot),
               helper.complex_enclosed_types(prot=prot),
               helper.constructors(prot=prot),
               helper.destructors(prot=prot),
               helper.operators(prot=prot),
               helper.variables(prot=prot),
               helper.static_methods(prot=prot),
               helper.methods(prot=prot),
               element.sections):
        break
else:
    return STOP_RENDERING
%>
################################################################################# Overview table ##
[cols='h,5a']
|===
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
% for section_title, section_text in element.sections.items():
| ${section_title}
| ${section_text | tc}

% endfor
% for prot in ("public", "protected", "private"):
###################################################################################################
% if (has_any(helper.simple_enclosed_types(prot=prot), helper.complex_enclosed_types(prot=prot))):
|*${prot.capitalize()} Enclosed Types*
|
% for enclosed in chain(helper.simple_enclosed_types(prot=prot), helper.complex_enclosed_types(prot=prot)):
`<<${enclosed.id},++${enclosed.name}++>>`::
${enclosed.brief | tc}
% endfor

% endif
###################################################################################################
% if has(helper.constructors(prot=prot)):
|*${prot.capitalize()} Constructors*
|
% for constructor in helper.constructors(prot=prot):
`<<${constructor.id},++${constructor.name}${helper.type_list(constructor.params)}++>>`::
${constructor.brief | tc}
% endfor

% endif
###################################################################################################
% if has(helper.destructors(prot=prot)):
|*${prot.capitalize()} Destructors*
|
% for destructor in helper.destructors(prot=prot):
`<<${destructor.id},++${destructor.name}()++>>`::
${destructor.brief | tc}
% endfor

% endif
###################################################################################################
% if has(helper.operators(prot=prot)):
|*${prot.capitalize()} Operators*
|
% for operator in helper.operators(prot=prot):
`<<${operator.id},++${operator.name}${helper.type_list(operator.params)}++>>`::
${operator.brief | tc}
% endfor

% endif
###################################################################################################
% if has(helper.variables(prot=prot)):
|*${prot.capitalize()} Variables*
|
% for variable in helper.variables(prot=prot):
`<<${variable.id},++${variable.name}++>>`::
${variable.brief | tc}
% endfor
% endif
###################################################################################################
% if has(helper.static_methods(prot=prot)):
|*${prot.capitalize()} Static Methods*
|
% for method in helper.static_methods(prot=prot):
`<<${method.id},++static ${helper.print_ref(method.returns.type, link=False)} ${method.name}${helper.type_list(method.params)}++>>`::
${method.brief | tc}
% endfor

% endif
###################################################################################################
% if has(helper.methods(prot=prot)):
|*${prot.capitalize()} Methods*
|
% for method in helper.methods(prot=prot):
`<<${method.id},++${helper.print_ref(method.returns.type, link=False)} ${method.name}${helper.type_list(method.params)}${" const" if method.const else ""}++>>`::
${method.brief | tc}
% endfor

% endif
% endfor
|===

##################################################################### Enclosed enums and typedefs ##
% for prot in ("public", "protected", "private"):
% for enclosed in helper.simple_enclosed_types(prot=prot):
${api.insert_fragment(enclosed, insert_filter, leveloffset + 1)}
% endfor
% endfor

<%
for prot in ("public", "protected", "private"):
    if has_any(helper.simple_enclosed_types(prot=prot),
               helper.complex_enclosed_types(prot=prot),
               helper.constructors(prot=prot),
               helper.destructors(prot=prot),
               helper.operators(prot=prot),
               helper.variables(prot=prot),
               helper.static_methods(prot=prot),
               helper.methods(prot=prot)):
        break
else:
    return STOP_RENDERING
%>
${h2(leveloffset, "Members")}

% for prot in ("public", "protected", "private"):
################################################################################### Constructors ##
% for constructor in helper.constructors(prot=prot):
${api.insert_fragment(constructor, insert_filter, kind_override="method", leveloffset=leveloffset + 2)}
'''
% endfor
#################################################################################### Destructors ##
% for destructor in helper.destructors(prot=prot):
${api.insert_fragment(destructor, insert_filter, kind_override="method", leveloffset=leveloffset + 2)}
'''
% endfor
###################################################################################### Operators ##
% for operator in helper.operators(prot=prot):
${api.insert_fragment(operator, insert_filter, kind_override="method", leveloffset=leveloffset + 2)}
'''
% endfor
###################################################################################### Variables ##
% for variable in helper.variables(prot=prot):
[#${variable.id},reftext='${variable.name}']
${api.inserted(variable)}

[source,cpp,subs="-specialchars,macros+"]
----
${escape(helper.print_ref(variable.returns.type))} ${variable.name}
----

${variable.brief | tc}

${variable.description | tc}

'''
% endfor
################################################################################# Static methods ##
% for method in helper.static_methods(prot=prot):
${api.insert_fragment(method, insert_filter, kind_override="method", leveloffset=leveloffset + 2)}
'''
% endfor
######################################################################################## Methods ##
% for method in helper.methods(prot=prot):
${api.insert_fragment(method, insert_filter, kind_override="method", leveloffset=leveloffset + 2)}
'''
% endfor
% endfor

############################################################################# Inner/Nested types ##

% for prot in ("public", "protected", "private"):
% for enclosed in helper.complex_enclosed_types(prot=prot):
${api.insert_fragment(enclosed, insert_filter, leveloffset=leveloffset + 1)}
% endfor
% endfor
