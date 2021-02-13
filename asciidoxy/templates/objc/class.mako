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
from asciidoxy.templates.objc.helpers import ObjcTemplateHelper
%>
<%
helper = ObjcTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.name}]]${element.name}
${api.inserted(element)}

[source,objectivec,subs="-specialchars,macros+"]
----
% if element.include:
#import &lt;${element.include}&gt;

% endif
@interface ${element.name}
----
${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===
% for prot in ("public", "protected", "private"):
###################################################################################################
% if has(helper.simple_enclosed_types(prot=prot)):
|*${prot.capitalize()} Enclosed Types*
|
% for enclosed in helper.simple_enclosed_types(prot=prot):
`<<${enclosed.id},+++${enclosed.name}+++>>`::
${enclosed.brief}
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
% if has(helper.class_methods(prot=prot)):
|*${prot.capitalize()} Class Methods*
|
% for method in helper.class_methods(prot=prot):
`<<${method.id},++++ ${method.name}+++>>`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(helper.methods(prot=prot)):
|*${prot.capitalize()} Methods*
|
% for method in helper.methods(prot=prot):
`<<${method.id},+++- ${method.name}+++>>`::
${method.brief}
% endfor

% endif
% endfor
|===

############################################################################ Simple inner types ##
% for enclosed in helper.simple_enclosed_types(prot=prot):
${api.insert_fragment(enclosed, insert_filter)}
% endfor

== Members
% for prot in ("public", "protected", "private"):
##################################################################################### Properties ##
% for prop in helper.properties(prot=prot):
[[${prop.id},${prop.name}]]
${api.inserted(prop)}
[source,objectivec,subs="-specialchars,macros+"]
----
@property() ${helper.print_ref(prop.returns.type)} ${prop.name}
----

${prop.brief}

${prop.description}

'''
% endfor
################################################################################## Class methods ##
% for method in helper.class_methods(prot=prot):
[[${method.id},${method.name}]]
${api.inserted(method)}
[source,objectivec,subs="-specialchars,macros+"]
----
${helper.method_signature(method)};
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
`(${helper.print_ref(param.type)})${param.name}`::
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
[source,objectivec,subs="-specialchars,macros+"]
----
${helper.method_signature(method)};
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
`(${helper.print_ref(param.type)})${param.name}`::
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
