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
from asciidoxy.templates.helpers import has
from asciidoxy.templates.java.helpers import JavaTemplateHelper
from asciidoxy.templates.kotlin.helpers import KotlinTemplateHelper
%>
<%
helper = KotlinTemplateHelper(api, element, insert_filter)
java_helper = JavaTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.name}]]${element.name}
${api.inserted(element)}

[source,kotlin,subs="-specialchars,macros+"]
----
class ${element.full_name}
----
${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===
% for prot in ("public", "protected", "internal", "private"):
###################################################################################################
% if has(helper.complex_enclosed_types(prot=prot)):
|*${prot.capitalize()} Enclosed Types*
|
% for enclosed in helper.complex_enclosed_types(prot=prot):
`<<${enclosed.id},+++${enclosed.name}+++>>`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(helper.constants(prot=prot)):
|*${prot.capitalize()} Constants*
|
% for constant in helper.constants(prot=prot):
`const val <<${constant.id},+++${constant.name}: ${constant.returns.type.name}+++>>`::
${constant.brief}
% endfor

% endif
###################################################################################################
% if has(helper.constructors(prot=prot)):
|*${prot.capitalize()} Constructors*
|
% for constructor in helper.constructors(prot=prot):
`<<${constructor.id},+++${constructor.name}${helper.type_list(constructor.params)}+++>>`::
${constructor.brief}
% endfor

% endif
###################################################################################################
% if has(helper.properties(prot=prot)):
|*${prot.capitalize()} Properties*
|
% for prop in helper.properties(prot=prot):
`<<${prop.id},+++${prop.name}+++>>`::
${prop.brief}
% endfor

% endif
###################################################################################################
% if has(java_helper.static_methods(prot=prot)):
|*${prot.capitalize()} Static Java Methods*
|
% for method in java_helper.static_methods(prot=prot):
`<<${method.id},+++static ${java_helper.print_ref(method.returns.type, link=False)} ${method.name}${java_helper.type_list(method.params)}+++>>`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(helper.methods(prot=prot)):
|*${prot.capitalize()} Methods*
|
% for method in helper.methods(prot=prot):
% if method.returns and method.returns.type.name != 'void':
`<<${method.id},+++${method.name}${helper.type_list(method.params)}: ${helper.print_ref(method.returns.type, link=False)}+++>>`::
% else:
`<<${method.id},+++${method.name}${helper.type_list(method.params)}+++>>`::
% endif
${method.brief}
% endfor

% endif
% endfor
|===

== Members
% for prot in ("public", "protected", "internal", "private"):
###################################################################################### Constants ##
% for constant in helper.constants(prot=prot):
[[${constant.id},${constant.name}]]
${api.inserted(constant)}
[source,kotlin,subs="-specialchars,macros+"]
----
const val ${constant.name}: ${constant.returns.type.name}
----

${constant.brief}

${constant.description}

'''
% endfor
################################################################################### Constructors ##
% for constructor in helper.constructors(prot=prot):
[[${constructor.id},${constructor.name}]]
${api.inserted(constructor)}
[source,kotlin,subs="-specialchars,macros+"]
----
${helper.method_signature(constructor)}
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
##################################################################################### Properties ##
% for prop in helper.properties(prot=prot):
[[${prop.id},${prop.name}]]
${api.inserted(prop)}
[source,kotlin,subs="-specialchars,macros+"]
----
val ${prop.name}: ${prop.returns.type.name}
----

${prop.brief}

${prop.description}

'''
% endfor
################################################################################# Static methods ##
% for method in java_helper.static_methods(prot=prot):
[[${method.id},${method.name}]]
${api.inserted(method)}
[source,java,subs="-specialchars,macros+"]
----
${java_helper.method_signature(method)}
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
`${java_helper.print_ref(param.type)} ${param.name}`::
${param.description}

% endfor
% endif
% if method.returns and method.returns.type.name != "void":
| Returns
|
`${java_helper.print_ref(method.returns.type)}`::
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
[source,kotlin,subs="-specialchars,macros+"]
----
${helper.method_signature(method)}
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
`${param.name}: ${helper.print_ref(param.type)}`::
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

############################################################################# Inner/Nested types ##

% for enclosed in helper.complex_enclosed_types(prot=prot):
${api.insert_fragment(enclosed, insert_filter)}
% endfor
% endfor
