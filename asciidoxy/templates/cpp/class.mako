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

################################################################################ Helper includes ##
<%!
from asciidoxy.templates.helpers import has, has_any
from asciidoxy.templates.cpp.helpers import CppTemplateHelper
from itertools import chain
%>
<%
helper = CppTemplateHelper(api_context, element, insert_filter)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.full_name}]]${element.name}
${api_context.insert(element)}

[source,cpp,subs="-specialchars,macros+"]
----
% if element.include:
#include &lt;${element.include}&gt;

% endif
${"struct" if element.kind == "struct" else "class"} ${element.full_name}
----
${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===

###################################################################################################
% if (has_any(helper.public_simple_enclosed_types(), helper.public_complex_enclosed_types())):
|*Enclosed types*
|
% for enclosed in chain(helper.public_simple_enclosed_types(), helper.public_complex_enclosed_types()):
`xref:${enclosed.id}[${enclosed.name}]`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_constructors()):
|*Constructors*
|
% for constructor in helper.public_constructors():
`xref:${constructor.id}[${constructor.name}${helper.type_list(constructor.params)}]`::
${constructor.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_destructors()):
|*Destructors*
|
% for destructor in helper.public_destructors():
`xref:${destructor.id}[${destructor.name}()]`::
${destructor.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_operators()):
|*Operators*
|
% for operator in helper.public_operators():
`xref:${operator.id}[${operator.name}${helper.type_list(operator.params)}]`::
${operator.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_variables()):
|*Variables*
|
% for variable in helper.public_variables():
`xref:${variable.id}[${variable.name}]`::
${variable.brief}
% endfor
% endif
###################################################################################################
% if has(helper.public_static_methods()):
|*Static methods*
|
% for method in helper.public_static_methods():
`xref:${method.id}[static ${helper.print_ref(method.returns.type, link=False)} ${method.name}${helper.type_list(method.params)}]`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_methods()):
|*Methods*
|
% for method in helper.public_methods():
`xref:${method.id}[${helper.print_ref(method.returns.type, link=False)} ${method.name}${helper.type_list(method.params)}${" const" if method.const else ""}]`::
${method.brief}
% endfor

% endif
|===

##################################################################### Enclosed enums and typedefs ##
% for enclosed in helper.public_simple_enclosed_types():
${api.insert_fragment(enclosed, insert_filter)}
% endfor

== Members

################################################################################### Constructors ##
% for constructor in helper.public_constructors():
${api.insert_fragment(constructor, insert_filter, kind_override="method")}
'''
% endfor
#################################################################################### Destructors ##
% for destructor in helper.public_destructors():
${api.insert_fragment(destructor, insert_filter, kind_override="method")}
'''
% endfor
###################################################################################### Operators ##
% for operator in helper.public_operators():
${api.insert_fragment(operator, insert_filter, kind_override="method")}
'''
% endfor
###################################################################################### Variables ##
% for variable in helper.public_variables():
[[${variable.id},${variable.name}]]
${api_context.insert(variable)}

[source,cpp,subs="-specialchars,macros+"]
----
${helper.print_ref(variable.returns.type)} ${variable.name}
----

${variable.brief}

${variable.description}

'''
% endfor
################################################################################# Static methods ##
% for method in helper.public_static_methods():
${api.insert_fragment(method, insert_filter, kind_override="method")}
'''
% endfor
######################################################################################## Methods ##
% for method in helper.public_methods():
${api.insert_fragment(method, insert_filter, kind_override="method")}
'''
% endfor

############################################################################# Inner/Nested types ##

% for enclosed in helper.public_complex_enclosed_types():
${api.insert_fragment(enclosed, insert_filter)}
% endfor
