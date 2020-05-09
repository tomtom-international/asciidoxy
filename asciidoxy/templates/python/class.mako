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
from asciidoxy.templates.helpers import (link_from_ref, print_ref, has, type_and_name, chain)
from asciidoxy.templates.python.helpers import (public_static_methods, public_methods,
public_constructors, public_variables, public_enclosed_types)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.full_name}]]${element.name}
${api_context.insert(element)}

[source,python,subs="-specialchars,macros+"]
----
class ${element.full_name}
----
${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===

###################################################################################################
% if has(public_enclosed_types(element, insert_filter)):
|*Enclosed types*
|
% for enclosed in public_enclosed_types(element, insert_filter):
`xref:${enclosed.id}[+++${enclosed.name}+++]`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(public_constructors(element, insert_filter)):
|*Constructors*
|
% for constructor in public_constructors(element, insert_filter):
`xref:${constructor.id}[+++${constructor.name}+++]`::
${constructor.brief}
% endfor

% endif
###################################################################################################
% if has(public_variables(element, insert_filter)):
|*Variables*
|
% for variable in public_variables(element, insert_filter):
`xref:${variable.id}[+++${variable.name}+++]`::
${variable.brief}
% endfor
% endif
###################################################################################################
% if has(public_static_methods(element, insert_filter)):
|*Static methods*
|
% for method in public_static_methods(element, insert_filter):
`xref:${method.id}[+++${method.name}+++]`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(public_methods(element, insert_filter)):
|*Methods*
|
% for method in public_methods(element, insert_filter):
`xref:${method.id}[+++${method.name}+++]`::
${method.brief}
% endfor

% endif
|===

== Members

################################################################################### Constructors ##
% for constructor in public_constructors(element, insert_filter):
${api.insert_fragment(constructor, insert_filter)}
'''
% endfor
###################################################################################### Variables ##
% for variable in public_variables(element, insert_filter):
[[${variable.id},${variable.name}]]
${api_context.insert(variable)}

[source,python,subs="-specialchars,macros+"]
----
% if variable.returns is not None:
${variable.name}: ${link_from_ref(variable.returns.type, api_context)}
% else:
${variable.name}
% endif
----

${variable.brief}

${variable.description}

'''
% endfor
################################################################################# Static methods ##
% for method in public_static_methods(element, insert_filter):
${api.insert_fragment(method, insert_filter)}
'''
% endfor
######################################################################################## Methods ##
% for method in public_methods(element, insert_filter):
${api.insert_fragment(method, insert_filter)}
'''
% endfor

############################################################################# Inner/Nested types ##

% for enclosed in public_enclosed_types(element, insert_filter):
${api.insert_fragment(enclosed, insert_filter)}
% endfor

