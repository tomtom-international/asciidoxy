/*
 * Copyright (C) 2019-2021, TomTom (http://tomtom.com).
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * \file
 */

namespace asciidoxy {
namespace descriptions {

/**
 * Description with all kinds of Doxygen styles.
 *
 * Several \a words in this \em sentence are \e italic.
 *
 * Several \b words in this \b sentence are \b bold.
 *
 * Also a \p some words in \c monotype.
 *
 */
class DoxygenVisualStyle {
};

/**
 * Description with some Doxygen lists.
 *
 * \arg \c AlignLeft left alignment.
 * \arg \c AlignCenter center alignment.
 * \arg \c AlignRight right alignment
 *
 * Another list:
 *
 * \li \b Bold.
 * \li \a Italic.
 * \li \c Monotype.
 */
class DoxygenList {
};

/**
 * Description with some code blocks.
 *
 * Python example:
 *
 * \code{.py}
 * class Python:
 *     pass
 * \endcode
 *
 * C++ example:
 *
 * \code{.cpp}
 * class Cpp {};
 * \endcode
 *
 * Unparsed code:
 *
 * \code{.unparsed}
 * Show this as-is please
 * \endcode
 *
 * Using the default language, C++ in this case:
 *
 * \code
 * class AlsoCpp {};
 * \endcode
 *
 * That's all folks!
 */
class CodeBlock {
};

/**
 * Description with several diagrams.
 *
 * Class relations expressed via an inline dot graph:
 * \dot
 * digraph example {
 *     node [shape=record, fontname=Helvetica, fontsize=10];
 *     b [ label="class B" URL="\ref DoxygenList"];
 *     c [ label="class C" URL="\ref CodeBlock"];
 *     b -> c [ arrowhead="open", style="dashed" ];
 * }
 * \enddot
 * Note that the classes in the above graph are clickable (in the HTML output).
 *
 * Receiver class. Can be used to receive and execute commands.
 * After execution of a command, the receiver will send an acknowledgment
 * \startuml
 *   Receiver<-Sender  : Command()
 *   Receiver-->Sender : Ack()
 * \enduml
 */
class Diagrams {
};

/**
 * \brief Using sections in the description.
 * \details This class demonstrates how all sections supported by Doxygen are handled.
 * \author Rob van der Most
 * \attention Be carefull with this class. It \b could blow up.
 * \bug Not all sections may be rendered correctly.
 * \copyright MIT license.
 * \date 28 August 2021
 * \deprecated This empty class should no longer be used.
 * \note Don't forget about \c this!
 * \pre The class should not exist yet.
 * \post The class suddenly exists.
 * \remark This class does not make much sense.
 * \since 0.7.6
 * \todo Create some content here.
 * \warning Do not use this class ever!
 */
class Sections {
};

/**
 * Complete documentation for a function or method.
 *
 * \param[in] first The first parameter.
 * \param[out] second The second parameter.
 * \param[in,out] third The third parameter.
 * \returns A status code
 * \retval 0 All is ok.
 * \retval 1 Something went wrong.
 * \exception std::logic_error Something is wrong with the logic.
 * \tparam Type The type to do something with.
 */
template<class Type>
int FunctionDocumentation(int first, double second, Type* third);

/**
 * Links to other elements.
 *
 * Some other test classes are:
 * \li CodeBlock for code blocks.
 * \li Diagrams for plantUML and Dot.
 * \li Sections for all kinds of sections.
 *
 * Of course there is also \ref FunctionDocumentation().
 */
class Links {
};

/**
 * Links to external locations.
 *
 * Our website is https://asciidoxy.org. You can use info@example.com for fake e-mail address 
 * examples.
 *
 * Don't forget to read our <a href="https://asciidoxy.org">documentation</a>.
 */
class ExternalLinks {
};

/**
 * Using HTML to create a complex table.
 *
 * <table>
 * <caption id="multi_row">Complex table</caption>
 * <tr><th>Column 1                      <th>Column 2        <th>Column 3
 * <tr><td rowspan="2">cell row=1+2,col=1<td>cell row=1,col=2<td>cell row=1,col=3
 * <tr><td rowspan="2">cell row=2+3,col=2                    <td>cell row=2,col=3
 * <tr><td>cell row=3,col=1                                  <td rowspan="2">cell row=3+4,col=3
 * <tr><td colspan="2">cell row=4,col=1+2
 * <tr><td>cell row=5,col=1              <td colspan="2">cell row=5,col=2+3
 * <tr><td colspan="2" rowspan="2">cell row=6+7,col=1+2      <td>cell row=6,col=3
 * <tr>                                                      <td>cell row=7,col=3
 * <tr><td>cell row=8,col=1              <td>cell row=8,col=2\n
 *   <table>
 *     <tr><td>Inner cell row=1,col=1<td>Inner cell row=1,col=2
 *     <tr><td>Inner cell row=2,col=1<td>Inner cell row=2,col=2
 *   </table>
 *   <td>cell row=8,col=3
 *   <ul>
 *     <li>Item 1
 *     <li>Item 2
 *   </ul>
 * </table>
 */
class ComplexHtmlTable {
};

}  // namespace descriptions
}  // namespace asciidoxy
