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
from asciidoxy.templates.python.helpers import PythonTemplateHelper
%>
<%
helper = PythonTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.full_name}]]${element.name}
${api.inserted(element)}

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
% if has(helper.complex_enclosed_types(prot="public")):
|*Enclosed types*
|
% for enclosed in helper.complex_enclosed_types(prot="public"):
`<<${enclosed.id},+++${enclosed.name}+++>>`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(helper.constructors(prot="public")):
|*Constructors*
|
% for constructor in helper.constructors(prot="public"):
`<<${constructor.id},+++${constructor.name}+++>>`::
${constructor.brief}
% endfor

% endif
###################################################################################################
% if has(helper.variables(prot="public")):
|*Variables*
|
% for variable in helper.variables(prot="public"):
`<<${variable.id},+++${variable.name}+++>>`::
${variable.brief}
% endfor
% endif
###################################################################################################
% if has(helper.static_methods(prot="public")):
|*Static methods*
|
% for method in helper.static_methods(prot="public"):
`<<${method.id},+++${method.name}+++>>`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(helper.methods(prot="public")):
|*Methods*
|
% for method in helper.methods(prot="public"):
`<<${method.id},+++${method.name}+++>>`::
${method.brief}
% endfor

% endif
|===

== Members

################################################################################### Constructors ##
% for constructor in helper.constructors(prot="public"):
${api.insert_fragment(constructor, insert_filter)}
'''
% endfor
###################################################################################### Variables ##
% for variable in helper.variables(prot="public"):
[[${variable.id},${variable.name}]]
${api.inserted(variable)}

[source,python,subs="-specialchars,macros+"]
----
% if variable.returns is not None:
${variable.name}: ${helper.print_ref(variable.returns.type)}
% else:
${variable.name}
% endif
----

${variable.brief}

${variable.description}

'''
% endfor
################################################################################# Static methods ##
% for method in helper.static_methods(prot="public"):
${api.insert_fragment(method, insert_filter)}
'''
% endfor
######################################################################################## Methods ##
% for method in helper.methods(prot="public"):
${api.insert_fragment(method, insert_filter)}
'''
% endfor

############################################################################# Inner/Nested types ##

% for enclosed in helper.complex_enclosed_types(prot="public"):
${api.insert_fragment(enclosed, insert_filter)}
% endfor

