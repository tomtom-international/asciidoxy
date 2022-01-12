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
from asciidoxy.generator.templates.objc.helpers import ObjcTemplateHelper
from html import escape
from itertools import chain
%>
<%
helper = ObjcTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
[#${element.id},reftext='${element.full_name}']
${h1(leveloffset, element.name)}
${api.inserted(element)}

[source,objectivec,subs="-specialchars,macros+"]
----
% if element.include:
#import &lt;${element.include}&gt;

% endif
@${"interface" if element.kind == "class" else element.kind} ${element.name}
----
${element.brief}

${element.description}

<%
for prot in ("public", "protected", "private"):
    if has_any(helper.simple_enclosed_types(prot=prot),
               helper.complex_enclosed_types(prot=prot),
               helper.properties(prot=prot),
               helper.class_methods(prot=prot),
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
% for prot in ("public", "protected", "private"):
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
% if has(helper.properties(prot=prot)):
|*${prot.capitalize()} Properties*
|
% for prop in helper.properties(prot=prot):
`<<${prop.id},++${prop.name}++>>`::
${prop.brief | tc}
% endfor

% endif
###################################################################################################
% if has(helper.class_methods(prot=prot)):
|*${prot.capitalize()} Class Methods*
|
% for method in helper.class_methods(prot=prot):
`<<${method.id},+++ ${method.name}++>>`::
${method.brief | tc}
% endfor

% endif
###################################################################################################
% if has(helper.methods(prot=prot)):
|*${prot.capitalize()} Methods*
|
% for method in helper.methods(prot=prot):
`<<${method.id},++- ${method.name}++>>`::
${method.brief | tc}
% endfor

% endif
% endfor
|===

############################################################################ Simple inner types ##
% for prot in ("public", "protected", "private"):
% for enclosed in helper.simple_enclosed_types(prot=prot):
${api.insert_fragment(enclosed, insert_filter, leveloffset=leveloffset + 1)}
% endfor
% endfor

<%
for prot in ("public", "protected", "private"):
    if has_any(helper.simple_enclosed_types(prot=prot),
               helper.complex_enclosed_types(prot=prot),
               helper.properties(prot=prot),
               helper.class_methods(prot=prot),
               helper.methods(prot=prot)):
        break
else:
    return STOP_RENDERING
%>
${h2(leveloffset, "Members")}
% for prot in ("public", "protected", "private"):
##################################################################################### Properties ##
% for prop in helper.properties(prot=prot):
[#${prop.id},reftext='${prop.name}']
${api.inserted(prop)}
[source,objectivec,subs="-specialchars,macros+"]
----
@property() ${escape(helper.print_ref(prop.returns.type))} ${prop.name}
----

${prop.brief | tc}

${prop.description | tc}

'''
% endfor
################################################################################## Class methods ##
% for method in helper.class_methods(prot=prot):
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
