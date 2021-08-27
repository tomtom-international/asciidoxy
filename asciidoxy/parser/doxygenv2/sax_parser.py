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


class DocumentHandler:
    @staticmethod
    def start_element(parser, name, attrs):
        if name == "compounddef":
            CompoundHandler.activate(parser, name, attrs)

    @staticmethod
    def end_element(parser, name):
        ...

    @staticmethod
    def characters(parser, content):
        ...


class CompoundHandler:
    @staticmethod
    def activate(parser, name, attrs):
        parser.push_handler(CompoundHandler)
        parser.push_model(Compound())

    @staticmethod
    def start_element(parser, name, attrs):
        ...

    @staticmethod
    def end_element(parser, name):
        if name == "compounddef":
            parser.pop_handler()
            print(parser.current_model())
            parser.pop_model()

    @staticmethod
    def characters(parser, content):
        ...


class DoxygenParser(LoggingContentHandler):
    def __init__(self):
        self._element_stack = []
        self._model_stack = []
        self._handler_stack = []

        self._locator = None

    def parse_file(self, path: Path):
        xml.sax.parse(str(path), self)

    def push_element(self, name):
        self._element_stack.append(name)

    def pop_element(self, name):
        assert self._element_stack[-1] == name
        self._element_stack.pop(-1)

    def current_element(self):
        return self._element_stack[-1]

    def push_model(self, model):
        self._model_stack.append(model)

    def pop_model(self):
        self._model_stack.pop(-1)

    def current_model(self):
        return self._model_stack[-1]

    def push_handler(self, handler):
        self._handler_stack.append(handler)

    def pop_handler(self):
        self._handler_stack.pop(-1)

    def current_handler(self):
        return self._handler_stack[-1]

    def setDocumentLocator(self, locator):
        self._locator = locator

    def startDocument(self):
        self.push_element("document")
        self.push_handler(DocumentHandler)

    def endDocument(self):
        self.pop_element("document")
        self.pop_handler()

    def startElement(self, name, attrs):
        self.push_element(name)
        print("::".join(self._element_stack), attrs.items())
        self.current_handler().start_element(self, name, attrs)

    def endElement(self, name):
        self.pop_element(name)
        self.current_handler().end_element(self, name)

    def characters(self, content):
        print("::".join(self._element_stack), repr(content))
        self.current_handler().characters(self, content)


if __name__ == "__main__":
    DoxygenParser().parse_file(Path(__file__).parent / "../../../tests/data/generated/xml/1.8.20/cpp/default/xml/classasciidoxy_1_1geometry_1_1_point.xml")
