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
from asciidoxy.templates.java.helpers import JavaTemplateHelper
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.full_name}]]${element.name}
${api.inserted(element)}

[source,java,subs="-specialchars,macros+"]
----
% if element.include:
import ${element.include}

% endif
enum ${element.full_name}
----

${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===

% for enum in JavaTemplateHelper(api, element, insert_filter).variables(prot="public"):
${api.inserted(enum)}
|
[[${enum.id},${enum.name}]]${enum.name}
|
${enum.brief}

${enum.description}

% endfor
|===
