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

<%!
from asciidoxy.templates.helpers import argument_list, link_from_ref
%>
= [[${element.id},${element.full_name}]]${element.name}
${api_context.insert(element)}


[source,objectivec,subs="-specialchars,macros+"]
----
typedef ${link_from_ref(element.returns.type, api_context)}(^ ${element.name}) ${argument_list(element.params, api_context)}
----
${element.brief}

${element.description}

