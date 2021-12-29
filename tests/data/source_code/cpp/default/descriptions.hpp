/*
 * Copyright (C) 2019, TomTom (http://tomtom.com).
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
 * For Doxygen no new line is needed between a paragraph and a code block.
 *
 * Python example:
 * \code{.py}
 * class Python:
 *     pass
 * \endcode
 *
 * C++ example:
 * \code{.cpp}
 * class Cpp {};
 * \endcode
 * That's it!
 */
class CodeBlockNoNewLine {
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

/**
 * Using Latex formulae.
 *
 * The distance between \f$(x_1,y_1)\f$ and \f$(x_2,y_2)\f$ is
 * \f$\sqrt{(x_2-x_1)^2+(y_2-y_1)^2}\f$.
 *
 * \f[
 *   |I_2|=\left| \int_{0}^T \psi(t) \left\{ u(a,t)-
 *               \int_{\gamma(t)}^a
 *               \frac{d\theta}{k(\theta,t)}
 *               \int_{a}^\theta c(\xi)u_t(\xi,t)\,d\xi
 *            \right\} dt
 *         \right|
 * \f]
 *
 * \f{eqnarray*}{
 *      g &=& \frac{Gm_2}{r^2} \\ 
 *        &=& \frac{(6.673 \times 10^{-11}\,\mbox{m}^3\,\mbox{kg}^{-1}\,
 *            \mbox{s}^{-2})(5.9736 \times 10^{24}\,\mbox{kg})}{(6371.01\,\mbox{km})^2} \\ 
 *        &=& 9.82066032\,\mbox{m/s}^2
 * \f}
 */
class Formulae {
};

/**
 * Include images in the documentation.
 *
 * A simple image:
 *
 * \image html Check-256.png
 *
 * We can have inline
 * \image{inline} html User-Group-256.png
 * images as well.
 *
 * For accessibility we should always provide a caption:
 *
 * \image html User-Profile-256.png "Image of a user"
 *
 * Size can be set:
 *
 * \image html User-Group-256.png "Image of a user group" width=50 height=100
 */
class Images {
};

/**
 * Doxygen supports MarkDown.
 *
 * A simple paragraph.
 *
 * And another paragraph.
 *
 * Header
 * ======
 *
 * > Perfection is achieved, not when there is nothing more to add, but when there is nothing left
 * > to take away.
 *
 * - List can be made with different bullets
 *   + And can be nested
 *   + Multiple levels
 *     * Even this deep
 *     * Do we really need that?
 *   + I guess we do
 * - We should support this.
 *
 * Subheader
 * ---------
 *
 * 1. First item
 * 2. Second item
 * 3. Third item
 *
 * ---
 *
 * Some example code:
 *
 *     int answer = 42;
 *
 *
 * ~~This is not right~~
 *
 * | Right | Center | Left  |
 * | ----: | :----: | :---- |
 * | 10    | 10     | 10    |
 * | 1000  | 1000   | 1000  |
 *
 */
class MarkDown {
};

/**
 * Combining ordered and unordered lists.
 *
 * 1. Linux
 *    - ArchLinux
 *    - Ubuntu
 *    - Fedora
 * 2. BSD
 *    - FreeBSD
 *    - NetBSD
 */
class HybridList {
};

/**
 * Dashes are sometimes handled specially.
 *
 * This is a long dash: ---
 *
 * Some shorter dashes: ...--road1--road2--...
 */
class Dashes {
};

/**
 * Developers can get creative with Ascii art in comments.
 *
 * <pre>
 * Arcs:    O---------------->O--------->O----------------------->O
 * Stretch: |            ^======================^
 * Route:   |       ^-------------------------------------^
 *          |     Origin                             Destination
 *          |<---------->|               |<---->|
 * Offsets:  front_offset               back_offset
 * </pre>
 */
class AsciiArt {
};


/**
 * Some special characters have specific XML representations.
 *
 * An angle between -90&deg; and +90&deg;.
 *
 * This is&nbsp;a non breaking&nbsp;space.
 *
 * There are a lot of special characters, &plusmn;250: &alpha;&beta;&frac14;
 */
class SpecialCharacters {
};

/**
 * HTML headings are supported as well.
 *
 * <h1>The top level heading.</h1>
 * An introduction to the topic.
 *
 * <h2>First subheading.</h2>
 * More text.
 *
 * <h2>Another subheading.</h2>
 * Even more text.
 */
class HtmlHeadings {
};

/**
 * Some extra visual styles are possible with HTML.
 *
 * CO<sub>2</sub> and X<sup>2</sup>.
 *
 * <ins>Inserted text</ins><br/>
 * <del>Deleted test</del>
 *
 * <u>Underlined text</u>
 *
 * <s>Put a line through this</s>
 *
 * <small>Small text</small>
 *
 * <center>
 * Some centered paragraphs.
 *
 * Nice in the center here.
 * </center>
 */
class HtmlStyles {
};

/**
 * Manual anchors can be inserted in the code.
 *
 * @anchor MANUAL_ANCHOR
 *
 * You can refer back to the \ref MANUAL_ANCHOR "anchor".
 */
class Anchor {
};

/**
 * Parblocks are used to add multiple paragraphs to commands that only accept a single parameter.
 *
 * @param parameter
 * @parblock
 * First paragraph about the parameter.
 *
 * Second paragraph about the parameter.
 * @endparblock
 */
void ParBlock(int parameter);

/**
 * Some blocks are only to be included in specific output types.
 *
 * @docbookonly
 * Don't include docbook stuff.
 * @enddocbookonly
 *
 * @manonly
 * Don't include man stuff.
 * @endmanonly
 *
 * @htmlonly
 * Include HTML only text.
 * @endhtmlonly
 *
 * @latexonly
 * Do not include Latex here.
 * @endlatexonly
 *
 * @rtfonly
 * RTF is not welcome either.
 * @endrtfonly
 *
 * @xmlonly
 * XML text should be included.
 * @endxmlonly
 */
class OutputSpecificBlocks {
};

/**
 * @copydoc FunctionDocumentation()
 */
template<class Type>
int CopyDoc(int first, double second, Type* third);

/**
 * Emoji can be used in Doxygen.
 *
 * \emoji smile I am happy
 *
 * \emoji cry I am sad
 *
 * \emoji star
 */
class Emoji {
};

}  // namespace descriptions
}  // namespace asciidoxy
