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

######################################################################## Header and introduction ##
= [[${element.id},${element.full_name}]]${element.name}
${api_context.insert(element)}

[source,cpp,subs="-specialchars,macros+"]
----
% if element.include:
#include &lt;${element.include}&gt;

% endif
enum ${element.full_name}
----

${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===

% for value in insert_filter.enum_values(element):
${api_context.insert(value)}
| [[${value.id},${value.name}]]${value.name} ${value.initializer}
|
${value.brief}

${value.description}

% endfor
|===
