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
from asciidoxy.templates.helpers import (link_from_ref, has)
from asciidoxy.templates.objc.helpers import (objc_method_signature, public_methods,
public_class_methods, public_properties, public_simple_enclosed_types)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.name}]]${element.name}
${api_context.insert(element)}

[source,objectivec,subs="-specialchars,macros+"]
----
% if element.include:
#import &lt;${element.include}&gt;

% endif
@protocol ${element.name}
----
${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===

###################################################################################################
% if has(public_simple_enclosed_types(element, insert_filter)):
|*Enclosed types*
|
% for enclosed in public_simple_enclosed_types(element, insert_filter):
`xref:${enclosed.id}[${enclosed.name}]`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(public_properties(element, insert_filter)):
|*Properties*
|
% for prop in public_properties(element, insert_filter):
`xref:${prop.id}[${prop.name}]`::
${prop.brief}
% endfor

% endif
###################################################################################################
% if has(public_class_methods(element, insert_filter)):
|*Class methods*
|
% for method in public_class_methods(element, insert_filter):
`xref:${method.id}[${method.name}]`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(public_methods(element, insert_filter)):
|*Methods*
|
% for method in public_methods(element, insert_filter):
`xref:${method.id}[${method.name}]`::
${method.brief}
% endfor

% endif
|===

################################################################################# Enclosed types ##
% for enclosed in public_simple_enclosed_types(element, insert_filter):
${api.insert_fragment(enclosed, insert_filter)}
% endfor

== Members

##################################################################################### Properties ##
% for prop in public_properties(element, insert_filter):
[[${prop.id},${prop.name}]]
${api_context.insert(prop)}
[source,objectivec,subs="-specialchars,macros+"]
----
@property() ${link_from_ref(prop.returns.type, api_context)} ${prop.name}
----

${prop.brief}

${prop.description}

'''
% endfor
################################################################################## Class methods ##
% for method in public_class_methods(element, insert_filter):
[[${method.id},${method.name}]]
${api_context.insert(method)}
[source,objectivec,subs="-specialchars,macros+"]
----
${objc_method_signature(method, api_context)};
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
`(${link_from_ref(param.type, api_context)})${param.name}`::
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
[source,objectivec,subs="-specialchars,macros+"]
----
${objc_method_signature(method, api_context)};
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
`(${link_from_ref(param.type, api_context)})${param.name}`::
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
