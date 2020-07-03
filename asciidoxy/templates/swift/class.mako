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
from asciidoxy.templates.swift.helpers import SwiftTemplateHelper
%>
<%
helper = SwiftTemplateHelper(api_context, element, insert_filter)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.name}]]${element.name}
${api_context.insert(element)}

[source,swift,subs="-specialchars,macros+"]
----
${element.kind} ${element.name}
----
${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===

###################################################################################################
% if has(helper.public_simple_enclosed_types()):
|*Enclosed types*
|
% for enclosed in helper.public_simple_enclosed_types():
`xref:${enclosed.id}[${enclosed.name}]`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_constructors()):
|*Constructors*
|
% for constructor in helper.public_constructors():
`xref:${constructor.id}[${constructor.name}]`::
${constructor.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_properties()):
|*Properties*
|
% for prop in helper.public_properties():
`xref:${prop.id}[${prop.name}]`::
${prop.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_class_methods()):
|*Class methods*
|
% for method in helper.public_class_methods():
`xref:${method.id}[${method.name}]`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_methods()):
|*Methods*
|
% for method in helper.public_methods():
`xref:${method.id}[${method.name}]`::
${method.brief}
% endfor

% endif
|===

############################################################################ Simple inner types ##
% for enclosed in helper.public_simple_enclosed_types():
${api.insert_fragment(enclosed, insert_filter)}
% endfor

== Members

################################################################################### Constructors ##
% for constructor in helper.public_constructors():
[[${constructor.id},${constructor.name}]]
${api_context.insert(constructor)}
[source,swift,subs="-specialchars,macros+"]
----
${helper.method_signature(constructor)};
----

${constructor.brief}

${constructor.description}

% if constructor.params or constructor.exceptions or constructor.returns:
[cols='h,5a']
|===
% if constructor.params:
| Parameters
|
% for param in constructor.params:
`${helper.type_and_name(param)}`::
${param.description}

% endfor
% endif
% if constructor.exceptions:
| Throws
|
% for exception in constructor.exceptions:
`${exception.type.name}`::
${exception.description}

% endfor
%endif
|===
% endif

'''
% endfor
##################################################################################### Properties ##
% for prop in helper.public_properties():
[[${prop.id},${prop.name}]]
${api_context.insert(prop)}
[source,swift,subs="-specialchars,macros+"]
----
var ${prop.name}: ${helper.print_ref(prop.returns.type)}
----

${prop.brief}

${prop.description}

'''
% endfor
################################################################################## Class methods ##
% for method in helper.public_class_methods():
[[${method.id},${method.name}]]
${api_context.insert(method)}
[source,swift,subs="-specialchars,macros+"]
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
`${helper.type_and_name(param)}`::
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
% for method in helper.public_methods():
[[${method.id},${method.name}]]
${api_context.insert(method)}
[source,swift,subs="-specialchars,macros+"]
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
`${helper.type_and_name(param)}`::
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
