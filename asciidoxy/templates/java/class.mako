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
from asciidoxy.templates.helpers import has, has_any
from asciidoxy.templates.java.helpers import JavaTemplateHelper
from html import escape
from itertools import chain
%>
<%
helper = JavaTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.name}]]${element.name}
${api.inserted(element)}

[source,java,subs="-specialchars,macros+"]
----
class ${element.full_name}
----
${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===
% for prot in ("public", "protected", "default", "private"):
###################################################################################################
% if has_any(helper.simple_enclosed_types(prot=prot), helper.complex_enclosed_types(prot=prot)):
|*${prot.capitalize()} Enclosed Types*
|
% for enclosed in chain(helper.simple_enclosed_types(prot=prot), helper.complex_enclosed_types(prot=prot)):
`<<${enclosed.id},++${enclosed.name}++>>`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(helper.constants(prot=prot)):
|*${prot.capitalize()} Constants*
|
% for constant in helper.constants(prot=prot):
`<<${constant.id},++${constant.returns.type.name} ${constant.name}++>>`::
${constant.brief}
% endfor

% endif
###################################################################################################
% if has(helper.constructors(prot=prot)):
|*${prot.capitalize()} Constructors*
|
% for constructor in helper.constructors(prot=prot):
`<<${constructor.id},++${constructor.name}${helper.type_list(constructor.params)}++>>`::
${constructor.brief}
% endfor

% endif
###################################################################################################
% if has(helper.static_methods(prot=prot)):
|*${prot.capitalize()} Static Methods*
|
% for method in helper.static_methods(prot=prot):
`<<${method.id},++static ${helper.print_ref(method.returns.type, link=False)} ${method.name}${helper.type_list(method.params)}++>>`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(helper.methods(prot=prot)):
|*${prot.capitalize()} Methods*
|
% for method in helper.methods(prot=prot):
`<<${method.id},++${helper.print_ref(method.returns.type, link=False)} ${method.name}${helper.type_list(method.params)}++>>`::
${method.brief}
% endfor

% endif
%endfor
|===

########################################################################## Enclosed simple types ##
% for prot in ("public", "protected", "private"):
% for enclosed in helper.simple_enclosed_types(prot=prot):
${api.insert_fragment(enclosed, insert_filter)}
% endfor
% endfor

== Members
% for prot in ("public", "protected", "private"):
###################################################################################### Constants ##
% for constant in helper.constants(prot=prot):
[[${constant.id},${constant.name}]]
${api.inserted(constant)}
[source,java,subs="-specialchars,macros+"]
----
${constant.returns.type.name} ${constant.name}
----

${constant.brief}

${constant.description}

'''
% endfor
################################################################################### Constructors ##
% for constructor in helper.constructors(prot=prot):
[[${constructor.id},${constructor.name}]]
${api.inserted(constructor)}
[source,java,subs="-specialchars,macros+"]
----
${escape(helper.method_signature(constructor))}
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
`${helper.print_ref(param.type)} ${param.name}`::
${param.description}

% endfor
% endif
% if constructor.exceptions:
| Throws
|
% for exception in constructor.exceptions:
`${helper.print_ref(exception.type)}`::
${exception.description}

% endfor
%endif
|===
% endif
'''
% endfor
################################################################################# Static methods ##
% for method in helper.static_methods(prot=prot):
[[${method.id},${method.name}]]
${api.inserted(method)}
[source,java,subs="-specialchars,macros+"]
----
${escape(helper.method_signature(method))}
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
`${helper.print_ref(param.type)} ${param.name}`::
${param.description}

% endfor
% endif
% if method.returns and method.returns.type.name != "void":
| Returns
|
`${helper.print_ref(method.returns.type)}`::
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
% for method in helper.methods(prot=prot):
[[${method.id},${method.name}]]
${api.inserted(method)}
[source,java,subs="-specialchars,macros+"]
----
${escape(helper.method_signature(method))}
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
`${helper.print_ref(param.type)} ${param.name}`::
${param.description}

% endfor
% endif
% if method.returns and method.returns.type.name != "void":
| Returns
|
`${helper.print_ref(method.returns.type)}`::
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
% endfor

############################################################################# Inner/Nested types ##

% for prot in ("public", "protected", "private"):
% for enclosed in helper.complex_enclosed_types(prot=prot):
${api.insert_fragment(enclosed, insert_filter)}
% endfor
% endfor
