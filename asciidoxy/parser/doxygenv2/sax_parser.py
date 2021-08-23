import xml.sax
from xml.sax.handler import ContentHandler
from pathlib import Path

from ...model import Compound


class LoggingContentHandler(ContentHandler):
    def setDocumentLocator(self, locator):
        print(f"{self.__class__.__name__}: Unhandled setDocumentLocator({locator})")

    def startDocument(self):
        print(f"{self.__class__.__name__}: Unhandled startDocument")

    def endDocument(self):
        print(f"{self.__class__.__name__}: Unhandled endDocument")

    def startPrefixMapping(self, prefix, uri):
        print(f"{self.__class__.__name__}: Unhandled startPrefixMapping({prefix}, {uri})")

    def endPrefixMapping(self, prefix):
        print(f"{self.__class__.__name__}: Unhandled endPrefixMapping({prefix})")

    def startElement(self, name, attrs):
        print(f"{self.__class__.__name__}: Unhandled startElement({name}, {attrs.items()})")

    def endElement(self, name):
        print(f"{self.__class__.__name__}: Unhandled endElement({name})")

    def startElementNS(self, name, qname, attrs):
        print(f"{self.__class__.__name__}: Unhandled startElementNS({name}, {qname}, {attrs.items()})")

    def endElementNS(self, name, qname):
        print(f"{self.__class__.__name__}: Unhandled endElementNS({name}, {qname})")

    def characters(self, content):
        print(f"{self.__class__.__name__}: Unhandled characters({repr(content)})")

    def ignorableWhitespace(self, whitespace):
        print(f"{self.__class__.__name__}: Unhandled ignorableWhitespace({repr(whitespace)})")

    def processingInstruction(self, target, data):
        print(f"{self.__class__.__name__}: Unhandled processingInstruction({target}, {data})")

    def skippedEntity(self, name):
        print(f"{self.__class__.__name__}: Unhandled skippedEntity({name})")


class DocumentContentHandler(LoggingContentHandler):
    def __init__(self, parser):
        self._parser = parser

    def endDocument(self):
        self._parser.pop_handler()

    def startElement(self, name, attrs):
        if name == "compounddef":
            self._parser.push_handler(CompoundContentHandler(self._parser, attrs))

        elif name == "doxygen":
            self._doxygen_version = attrs.get("version")

        else:
            super().startElement(name, attrs)


class CompoundContentHandler(LoggingContentHandler):
    def __init__(self, parser, attrs):
        self._parser = parser
        self._compound = Compound(id=attrs.get("id"), kind=attrs.get("kind"),
                                  language=attrs.get("language"), prot=attrs.get("prot"))

    def startElement(self, name, attrs):
        if name == "compoundname":
            self._parser.push_handler(StringAttributeContentHandler(self._parser,
                                                                    self._compound,
                                                                    "full_name"))
        else:
            super().startElement(name, attrs)

    def endElement(self, name):
        if name == "compounddef":
            self._parser.pop_handler()
            print(self._compound)
        else:
            super().endElement(name)


class StringAttributeContentHandler(LoggingContentHandler):
    def __init__(self, parser, parent, attribute_name):
        self._parser = parser
        self._parent = parent
        self._attribute_name = attribute_name
        self._data = ""

    def startElement(self, name, attrs):
        assert False, "Cannot handle this"

    def endElement(self, name):
        setattr(self._parent, self._attribute_name, self._data.strip())
        self._parser.pop_handler()

    def characters(self, content):
        self._data += content


class DoxygenParser(LoggingContentHandler):
    def __init__(self):
        self._handler_stack = []
        self._locator = None

    def parse_file(self, path: Path):
        xml.sax.parse(str(path), self)

    def pop_handler(self):
        self._handler_stack.pop(-1)

    def push_handler(self, handler):
        self._handler_stack.append(handler)

    def setDocumentLocator(self, locator):
        self._locator = locator

    def startDocument(self):
        self._handler_stack.append(DocumentContentHandler(self))

    def endDocument(self):
        self._handler_stack[-1].endDocument()

    def startElement(self, name, attrs):
        self._handler_stack[-1].startElement(name, attrs)

    def endElement(self, name):
        self._handler_stack[-1].endElement(name)

    def characters(self, content):
        self._handler_stack[-1].characters(content)


if __name__ == "__main__":
    DoxygenParser().parse_file(Path(__file__).parent / "../../../tests/data/generated/xml/1.8.20/cpp/default/xml/classasciidoxy_1_1geometry_1_1_point.xml")
