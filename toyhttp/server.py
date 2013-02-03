"""
The skeleton for a toy HTTP server implementation.

This implementation does not support persistent connections, chunked encoding,
multiple headers with same key, multi-line headers, etc..
"""

from twisted import internet
from twisted.protocols import basic
from twisted.internet.protocol import ServerFactory
class HTTP(basic.LineReceiver):
    """
    A toy implementation of the server-side HTTP protocol.

    This is the protocol you will be implementing that parses HTTP requests
    and writes out HTTP responses.
    """

    def __init__(self, handler, reactor=internet.reactor, *args, **kwargs):
        # save off handler function to call in requestReceived.
        self._handler = handler
        self.reactor = reactor
        self.lines = []

    def lineReceived(self, line):
        if line == "":
            line0Tokens = self.lines[0].split()
            headers = dict()
            for hline in self.lines[1:]:
                tokens = [x.strip() for x in hline.split(":")]
                headers[tokens[0]] = tokens[1]

            self.requestReceived(line0Tokens[0], line0Tokens[1], headers, "")
            self.lines = []
        else:
            self.lines.append(line)

    def _writeResponse(self, response):
        self.transport.write("HTTP/1.1 %d Reason\r\n"
                             "Content-Length: %d\r\n"
                             "content-type: text/plain\r\n"
                             "\r\n"
                             "%s" % 
                             (response.code, len(response.body),
                              response.body))
        self.transport.loseConnection()

    def requestReceived(self, method, path, headers, foo):
        self._writeResponse(self._handler(method, path, headers, foo))


class Response(object):
    """
    The response to an HTTP request.

    This will store the information needed to return a HTTP response.
    """
    #def __init__(self, *args, **kwargs):
    def __init__(self, statusCode, body, headers):
        self.code = statusCode
        self.body = body
        self.headers = headers

class HTTPFactory(ServerFactory):
    """
    A factory for HTTP servers.

    This will create instances of the HTTP class.
    """

    def __init__(self, handler, *args, **kwargs):
        self._handler = handler

    def buildProtocol(self, arg):
        return HTTP(self._handler)

