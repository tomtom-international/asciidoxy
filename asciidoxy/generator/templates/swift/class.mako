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
from asciidoxy.generator.templates.swift.helpers import SwiftTemplateHelper
from html import escape
from itertools import chain
%>
<%
helper = SwiftTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
[#${element.id},reftext='${element.full_name}']
${h1(leveloffset, element.name)}
${api.inserted(element)}

[source,swift,subs="-specialchars,macros+"]
----
${element.kind} ${element.name}
----
${element.brief}

${element.description}

<%
for prot in ("open", "public", "internal", "file-private", "private"):
    if has_any(helper.simple_enclosed_types(prot=prot),
               helper.complex_enclosed_types(prot=prot),
               helper.constructors(prot=prot),
               helper.properties(prot=prot),
               helper.type_methods(prot=prot),
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
% for prot in ("open", "public", "internal", "file-private", "private"):
###################################################################################################
% if has(helper.simple_enclosed_types(prot=prot)) or has(helper.complex_enclosed_types(prot=prot)):
|*${prot.capitalize()} Enclosed Types*
|
% for enclosed in chain(helper.simple_enclosed_types(prot=prot), helper.complex_enclosed_types(prot=prot)):
`<<${enclosed.id},++${enclosed.name}++>>`::
${enclosed.brief | tc}
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
% if has(helper.properties(prot=prot)):
|*${prot.capitalize()} Properties*
|
% for prop in helper.properties(prot=prot):
`<<${prop.id},++${prop.name}++>>`::
${prop.brief | tc}
% endfor

% endif
###################################################################################################
% if has(helper.type_methods(prot=prot)):
|*${prot.capitalize()} Type Methods*
|
% for method in helper.type_methods(prot=prot):
`<<${method.id},++${method.name}${helper.type_list(method.params)}++>>`::
${method.brief | tc}
% endfor

% endif
###################################################################################################
% if has(helper.methods(prot=prot)):
|*${prot.capitalize()} Methods*
|
% for method in helper.methods(prot=prot):
`<<${method.id},++${method.name}${helper.type_list(method.params)}++>>`::
${method.brief | tc}
% endfor

% endif
%endfor
|===

############################################################################ Simple inner types ##
% for prot in ("open", "public", "internal", "file-private", "private"):
% for enclosed in helper.simple_enclosed_types(prot=prot):
${api.insert_fragment(enclosed, insert_filter, leveloffset=leveloffset + 1)}
% endfor
%endfor

<%
for prot in ("open", "public", "internal", "file-private", "private"):
    if has_any(helper.simple_enclosed_types(prot=prot),
               helper.complex_enclosed_types(prot=prot),
               helper.constructors(prot=prot),
               helper.properties(prot=prot),
               helper.type_methods(prot=prot),
               helper.methods(prot=prot)):
        break
else:
    return STOP_RENDERING
%>
${h2(leveloffset, "Members")}
% for prot in ("open", "public", "internal", "file-private", "private"):
################################################################################### Constructors ##
% for constructor in helper.constructors(prot=prot):
${api.insert_fragment(constructor, insert_filter, kind_override="method", leveloffset=leveloffset + 2)}
'''
% endfor
##################################################################################### Properties ##
% for prop in helper.properties(prot=prot):
[#${prop.id},reftext='${prop.name}']
${api.inserted(prop)}
[source,swift,subs="-specialchars,macros+"]
----
var ${prop.name}: ${escape(helper.print_ref(prop.returns.type))}
----

${prop.brief | tc}

${prop.description | tc}

'''
% endfor
################################################################################### Type methods ##
% for method in helper.type_methods(prot=prot):
${api.insert_fragment(method, insert_filter, kind_override="method", leveloffset=leveloffset + 2)}
'''
% endfor
######################################################################################## Methods ##
% for method in helper.methods(prot=prot):
${api.insert_fragment(method, insert_filter, kind_override="method", leveloffset=leveloffset + 2)}
'''
% endfor

############################################################################# Inner/Nested types ##

% for enclosed in helper.complex_enclosed_types(prot=prot):
${api.insert_fragment(enclosed, insert_filter, leveloffset=leveloffset + 1)}
% endfor
% endfor
