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
from asciidoxy.generator.templates.helpers import has, has_any, h1, h2, tc
from asciidoxy.generator.templates.java.helpers import JavaTemplateHelper
from html import escape
from itertools import chain
%>
<%
helper = JavaTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
[#${element.id},reftext='${element.full_name}']
${h1(leveloffset, element.name)}
${api.inserted(element)}

[source,java,subs="-specialchars,macros+"]
----
${element.kind} ${element.full_name}
----
${element.brief}

${element.description}

<%
for prot in ("public", "protected", "default", "private"):
    if has_any(helper.simple_enclosed_types(prot=prot),
               helper.complex_enclosed_types(prot=prot),
               helper.constants(prot=prot),
               helper.constructors(prot=prot),
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
% for section_title, section_text in element.sections.items():
| ${section_title}
| ${section_text | tc}

% endfor
% for prot in ("public", "protected", "default", "private"):
###################################################################################################
% if has_any(helper.simple_enclosed_types(prot=prot), helper.complex_enclosed_types(prot=prot)):
|*${prot.capitalize()} Enclosed Types*
|
% for enclosed in chain(helper.simple_enclosed_types(prot=prot), helper.complex_enclosed_types(prot=prot)):
`<<${enclosed.id},++${enclosed.name}++>>`::
${enclosed.brief | tc}
% endfor

% endif
###################################################################################################
% if has(helper.constants(prot=prot)):
|*${prot.capitalize()} Constants*
|
% for constant in helper.constants(prot=prot):
`<<${constant.id},++${constant.returns.type.name} ${constant.name}++>>`::
${constant.brief | tc}
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
`<<${method.id},++${helper.print_ref(method.returns.type, link=False)} ${method.name}${helper.type_list(method.params)}++>>`::
${method.brief | tc}
% endfor

% endif
%endfor
|===

########################################################################## Enclosed simple types ##
% for prot in ("public", "protected", "private"):
% for enclosed in helper.simple_enclosed_types(prot=prot):
${api.insert_fragment(enclosed, insert_filter, leveloffset=leveloffset + 1)}
% endfor
% endfor

<%
for prot in ("public", "protected", "default", "private"):
    if has_any(helper.simple_enclosed_types(prot=prot),
               helper.complex_enclosed_types(prot=prot),
               helper.constants(prot=prot),
               helper.constructors(prot=prot),
               helper.static_methods(prot=prot),
               helper.methods(prot=prot)):
        break
else:
    return STOP_RENDERING
%>
${h2(leveloffset, "Members")}
% for prot in ("public", "protected", "private"):
###################################################################################### Constants ##
% for constant in helper.constants(prot=prot):
[#${constant.id},reftext=${constant.name}']
${api.inserted(constant)}
[source,java,subs="-specialchars,macros+"]
----
${constant.returns.type.name} ${constant.name}
----

${constant.brief | tc}

${constant.description | tc}

'''
% endfor
################################################################################### Constructors ##
% for constructor in helper.constructors(prot=prot):
${api.insert_fragment(constructor, insert_filter, kind_override="method", leveloffset=leveloffset + 2)}
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
