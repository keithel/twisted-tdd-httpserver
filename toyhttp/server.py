"""
The skeleton for a toy HTTP server implementation.

This implementation does not support persistent connections, chunked encoding,
multiple headers with same key, multi-line headers, etc..
"""

import twisted
from twisted.protocols import basic
from twisted.internet.protocol import ServerFactory
from twisted.internet.defer import Deferred
import re
class HTTP(basic.LineReceiver):
    """
    A toy implementation of the server-side HTTP protocol.

    This is the protocol you will be implementing that parses HTTP requests
    and writes out HTTP responses.
    """

    def __init__(self, handler, reactor=twisted.internet.reactor, *args, **kwargs):
        # save off handler function to call in requestReceived.
        self._handler = handler
        self.reactor = reactor
        self.lines = []

    def makeConnection(self, transport):
        basic.LineReceiver.makeConnection(self, transport)
        self.abortAfter60 = self.reactor.callLater(60, self.transport.abortConnection)

    def lineReceived(self, line):
        if line == "":
            #print "Lines received: " + str(self.lines)
            l0Toks = self.lines[0].split()
            headers = dict()
            for hline in self.lines[1:]:
                tokens = [x.strip() for x in hline.split(":")]
                headers[tokens[0]] = tokens[1]

            if len(l0Toks) == 3 and re.match("HTTP/\d\.\d", l0Toks[2]) != None:
                self.requestReceived(l0Toks[0], l0Toks[1], headers, "")
            else:
                self.badRequestReceived()
            self.lines = []
        else:
            self.lines.append(line)

    def _writeResponse(self, response):
        self.transport.write("HTTP/1.1 %d Reason\r\n"
                             "Content-Length: %d\r\n"
                             "content-type: text/html\r\n"
                             "\r\n"
                             "%s" % 
                             (response.code, len(response.body),
                              response.body))
        self.transport.loseConnection()

    def requestReceived(self, method, path, headers, foo):
        def internalServerError(e):
            twisted.python.log.err("Internal Server Error received: %s" % str(e))
            twisted.python.log.err(e)
            self._writeResponse(Response(500, "Internal Server Error", {}))

        def deferredCallback(response):
            try:
                response.code
                self._writeResponse(response)
            except Exception,e:
                internalServerError(e)

        # We have a full request now, cancel the 60 second abort.
        try: self.abortAfter60.cancel()
        except: pass

        try:
            handlerResult = self._handler(method, path, headers, foo)
            if isinstance(handlerResult, Deferred):
                handlerResult.addCallback(deferredCallback)
                handlerResult.addErrback(internalServerError)
            else:
                self._writeResponse(handlerResult)
        except RuntimeError,e:
            internalServerError(e)

    def badRequestReceived(self):
        self._writeResponse(Response(400, "", {}))


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

