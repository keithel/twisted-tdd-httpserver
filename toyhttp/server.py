"""
The skeleton for a toy HTTP server implementation.

This implementation does not support persistent connections, chunked encoding,
multiple headers with same key, multi-line headers, etc..
"""

from twisted.internet import protocol
class HTTP(protocol.Protocol):
    """
    A toy implementation of the server-side HTTP protocol.

    This is the protocol you will be implementing that parses HTTP requests
    and writes out HTTP responses.
    """

    def __init__(self, handler, reactor, *args, **kwargs):
        # save off handler function to call in requestReceived.
        self._handler = handler
        self.reactor = reactor

#    def makeConnection(self, transport):
#        pass

    def dataReceived(self, bytes):
        self.requestReceived("GET", "/foo/bar", {'Another':'thing', 'Key': 'val ue'}, "")

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

class HTTPFactory(object):
    """
    A factory for HTTP servers.

    This will create instances of the HTTP class.
    """

    def __init__(self, *args, **kwargs):
        pass
