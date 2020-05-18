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
from asciidoxy.templates.helpers import (link_from_ref, type_and_name, argument_list, has)
%>

= [[${element.id},${element.name}]]
${api_context.insert(element)}

[source,cpp,subs="-specialchars,macros+"]
----
${"static" if element.static else ""} \
${link_from_ref(element.returns.type, api_context) if element.returns else ""} \
${element.name}${argument_list(element.params, api_context)}
----
<%include file="/cpp/_function.mako"/>
