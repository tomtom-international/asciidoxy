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
from asciidoxy.templates.helpers import (link_from_ref, print_ref, argument_list, type_list, has)
from asciidoxy.templates.java.helpers import (public_methods, public_static_methods,
public_constructors, public_constants, public_complex_enclosed_types)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.name}]]${element.name}
${api_context.insert(element)}

[source,java,subs="-specialchars,macros+"]
----
class ${element.full_name}
----
${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===

###################################################################################################
% if has(public_complex_enclosed_types(element, insert_filter)):
|*Enclosed types*
|
% for enclosed in public_complex_enclosed_types(element, insert_filter):
`xref:${enclosed.id}[${enclosed.name}]`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(public_constructors(element, insert_filter)):
|*Constructors*
|
% for constructor in public_constructors(element, insert_filter):
`xref:${constructor.id}[${constructor.name}${type_list(constructor.params)}]`::
${constructor.brief}
% endfor

% endif
###################################################################################################
% if has(public_constants(element, insert_filter)):
|*Constants*
|
% for constant in public_constants(element, insert_filter):
`${constant.name}`::
${constant.description}
% endfor

% endif
###################################################################################################
% if has(public_static_methods(element, insert_filter)):
|*Static methods*
|
% for method in public_static_methods(element, insert_filter):
`xref:${method.id}[static ${print_ref(method.returns.type)} ${method.name}${type_list(method.params)}]`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(public_methods(element, insert_filter)):
|*Methods*
|
% for method in public_methods(element, insert_filter):
`xref:${method.id}[${print_ref(method.returns.type)} ${method.name}${type_list(method.params)}]`::
${method.brief}
% endfor

% endif
|===

== Members
################################################################################### Constructors ##
% for constructor in public_constructors(element, insert_filter):
[[${constructor.id},${constructor.name}]]
${api_context.insert(constructor)}
[source,java,subs="-specialchars,macros+"]
----
${constructor.name}${argument_list(constructor.params, api_context)}
----

${constructor.brief}

${constructor.description}

% if constructor.params or constructor.exceptions:
[cols='h,5a']
|===
% if constructor.params:
| Parameters
|
% for param in constructor.params:
`${link_from_ref(param.type, api_context)} ${param.name}`::
${param.description}

% endfor
% endif
% if constructor.exceptions:
| Throws
|
% for exception in constructor.exceptions:
`${link_from_ref(exception.type, api_context)}`::
${exception.description}

% endfor
%endif
|===
% endif
'''
% endfor
################################################################################# Static methods ##
% for method in public_static_methods(element, insert_filter):
[[${method.id},${method.name}]]
${api_context.insert(method)}
[source,java,subs="-specialchars,macros+"]
----
static ${link_from_ref(method.returns.type, api_context)} ${method.name}${argument_list(method.params, api_context)}
----

${method.brief}

${method.description}

% if method.params or method.exceptions or method.returns:
[cols='h,5a']
|===
% if method.params:
| Parameters
|
% for param in method.params:
`${link_from_ref(param.type, api_context)} ${param.name}`::
${param.description}

% endfor
% endif
% if method.returns and method.returns.type.name != "void":
| Returns
|
`${link_from_ref(method.returns.type, api_context)}`::
${method.returns.description}

% endif
% if method.exceptions:
| Throws
|
% for exception in method.exceptions:
`${exception.type.name}`::
${exception.description}

% endfor
%endif
|===
% endif
'''
% endfor
######################################################################################## Methods ##
% for method in public_methods(element, insert_filter):
[[${method.id},${method.name}]]
${api_context.insert(method)}
[source,java,subs="-specialchars,macros+"]
----
${link_from_ref(method.returns.type, api_context)} ${method.name}${argument_list(method.params, api_context)}
----

${method.brief}

${method.description}

% if method.params or method.exceptions or method.returns:
[cols='h,5a']
|===
% if method.params:
| Parameters
|
% for param in method.params:
`${link_from_ref(param.type, api_context)} ${param.name}`::
${param.description}

% endfor
% endif
% if method.returns and method.returns.type.name != "void":
| Returns
|
`${link_from_ref(method.returns.type, api_context)}`::
${method.returns.description}

% endif
% if method.exceptions:
| Throws
|
% for exception in method.exceptions:
`${exception.type.name}`::
${exception.description}

% endfor
%endif
|===
% endif
'''
% endfor

############################################################################# Inner/Nested types ##

% for enclosed in public_complex_enclosed_types(element, insert_filter):
${api.insert_fragment(enclosed, insert_filter)}
% endfor
