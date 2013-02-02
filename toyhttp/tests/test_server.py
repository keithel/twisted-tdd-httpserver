"""
Tests for toyhttp.server.
"""

from twisted.trial.unittest import TestCase
from twisted.test.proto_helpers import StringTransport
from twisted.internet import defer, reactor, task

from toyhttp.server import HTTP, HTTPFactory, Response


class AbortableTransport(StringTransport):
    """
    Fake transport with abortConnection() method.
    """
    aborting = False

    def abortConnection(self):
        self.aborting = True


class ResponseMixin(object):
    """
    Extra utility code for dealing with Response objects.
    """

    def assertResponsesEqual(self, a, b):
        """
        Assert the two given Response objects are equal.
        """
        self.assertEqual(a.code, b.code)
        self.assertEqual(a.body, b.body)
        self.assertEqual(a.headers, b.headers)


class Tests01_Protocol(TestCase, ResponseMixin):
    """
    Tests for server.HTTPServerProtocol.
    """

    def test_01_writeResponse(self):
        """
        L{HTTP._writeResponse} writes a HTTP response to the protocol's
        transport, then closes the connection. It takes a L{Response}
        object that is constructed with three arguments, a numberic response
        code and the body of the response, whose length is included as a
        content-length header, and additional headers (as a dictionary mapping
        keys to values).
        """
        protocol = HTTP(None, reactor=task.Clock())
        # Connect a fake, in-memory transport to the protocol:
        transport = AbortableTransport()
        protocol.makeConnection(transport)

        protocol._writeResponse(Response(200, "Response body!",
                                         {"content-type": "text/plain"}))
        self.assertEqual(transport.value(),
                         "HTTP/1.1 200 Reason\r\n"
                         "Content-Length: 14\r\n"
                         "content-type: text/plain\r\n"
                         "\r\n"
                         "Response body!")
        # The connection is closed once the response has been written,
        # i.e. transport.loseConnection() was called:
        self.assertEqual(transport.disconnecting, True)

    def test_02_handler(self):
        """
        L{HTTP.__init__} is called with a function as its argument. This
        function is called by L{HTTP.requestReceived} with the request
        parameters, and its response is passed to L{HTTP._writeResponse}.

        In other words, this function determines how the HTTP server processes
        and handles requests.
        """
        def handler(method, path, headers, body):
            self.assertEqual(method, "WOO")
            self.assertEqual(path, "/path")
            self.assertEqual(headers, {"Key": "value"})
            return Response(300, "hello", {"k": "v"})

        protocol = HTTP(handler, reactor=task.Clock())
        response = []
        protocol._writeResponse = lambda r: response.append(r)

        # Handler is stored as attribute as protocol:
        self.assertIdentical(protocol._handler, handler)
        # requestReceived calls handler, and then takes the results and passes
        # it to _writeResponse:
        protocol.requestReceived("WOO", "/path", {"Key": "value"}, "")
        self.assertResponsesEqual(response[0],
                                  Response(300, "hello", {"k": "v"}))

    def test_03_receiveRequest(self):
        """
        When L{HTTP.dataReceived} receives the bytes for a HTTP request,
        L{HTTP.requestRecieved} is called with the method and path.
        """
        protocol = HTTP(None, reactor=task.Clock())
        received = []
        protocol.requestReceived = lambda *args: received.append(args)

        # Hook up a fake in-memory transport:
        protocol.makeConnection(AbortableTransport())
        protocol.dataReceived("GET /foo/bar HTTP/1.1\r\n\r\n")
        self.assertEqual(received, [("GET", "/foo/bar", {}, "")])

    def test_04_receiveHeaders(self):
        """
        When L{HTTP.dataReceived} receives the bytes for a HTTP request,
        L{HTTP.requestRecieved} is called with a dictionary of headers.
        """
        protocol = HTTP(None, reactor=task.Clock())
        received = []
        protocol.requestReceived = lambda *args: received.append(args)

        protocol.makeConnection(AbortableTransport())
        protocol.dataReceived("GET /foo/bar HTTP/1.1\r\n"
                              "Key: val ue\r\n"
                              "Another: thing\r\n"
                              "\r\n")
        self.assertEqual(
            received,
            [("GET", "/foo/bar", {"Key": "val ue", "Another": "thing"}, "")])

    def test_05_receiveAfterFinalNewline(self):
        """
        L{HTTP.requestReceived} is only called after C{dataReceived} gets the
        final line with just '\r\n'.
        """
        protocol = HTTP(None, reactor=task.Clock())
        received = []
        protocol.requestReceived = lambda *args: received.append(args)

        protocol.makeConnection(AbortableTransport())
        protocol.dataReceived("HEAD /?x=y HTTP/1.1\r\n")
        self.assertEqual(received, [])
        protocol.dataReceived("\r\n")
        self.assertEqual(received, [("HEAD", "/?x=y", {}, "")])


class Tests02_Factory(TestCase):
    """
    Tests for L{HTTPFactory}.
    """

    def test_06_buildProtocol(self):
        """
        L{HTTPFactory.buildProtocol} returns an instance of L{HTTP},
        constructed with the function passed as an argument to
        L{HTTPFactory.__init__}.
        """
        handler = lambda *args: None
        factory = HTTPFactory(handler)
        protocol = factory.buildProtocol(None)
        self.assertIsInstance(protocol, HTTP)
        # Protocol was initialized with the handler:
        self.assertIdentical(protocol._handler, handler)

    @defer.inlineCallbacks
    def test_07_endToEnd(self):
        """
        The HTTP implementation is compatible with a real HTTP client, in so
        far as it can reply to a simple HTTP GET.
        """
        from twisted.web.client import getPage

        # Handler that returns the path as the body of the response:
        def handler(method, path, headers, body):
            return Response(200, path, {})

        port = reactor.listenTCP(0, HTTPFactory(handler), interface="127.0.0.1")
        self.addCleanup(port.stopListening)
        portNumber = port.getHost().port
        url = "http://127.0.0.1:%d/foo/bar" % (portNumber,)

        result = yield getPage(url)
        self.assertEqual(result, "/foo/bar")

    def test_08_demo(self):
        """
        If you've got tests 1-7 passing, you should be able to run demo1.py.
        """
    test_08_demo.skip = "This needs to be run manually."


class Tests03_Protocol(TestCase, ResponseMixin):
    """
    More protocol tests.

    These would be same test class as previous protocol TestCase, but are
    separated just to make order of tests clearer.
    """

    def test_09_badRequestResponse(self):
        """
        L{HTTP.badRequestReceived} writes a response with a 400 code ("Bad
        Client Request") using L{HTTP._writeResponse).
        """
        protocol = HTTP(None, reactor=task.Clock())
        response = []
        protocol._writeResponse = lambda r: response.append(r)

        protocol.badRequestReceived()
        self.assertResponsesEqual(response[0], Response(400, "", {}))

    def test_10_badRequests(self):
        """
        L{HTTP.dataReceived} calls L{HTTP.badRequestReceived} if it receives
        something it cannot parse.
        """
        def assertBadRequest(request):
            protocol = HTTP(None, reactor=task.Clock())
            protocol.makeConnection(AbortableTransport())
            result = []
            protocol.badRequestReceived = lambda: result.append(True)
            protocol.dataReceived(request)
            self.assertEqual(result, [True])

        # Missing HTTP version:
        assertBadRequest("GET /\r\n\r\n")
        # Too many items on first line:
        assertBadRequest("GET / HTTP/1.1 WOO\r\n\r\n")

    def test_11_handlerException(self):
        """
        If the handler throws an exception, L{HTTP.requestReceived} writes a
        response with error code 500 (internal server error), and the
        exception is logged.
        """
        def handler(method, path, headers, body):
            raise RuntimeError("I am a buggy handler!")

        protocol = HTTP(handler, reactor=task.Clock())
        response = []
        protocol._writeResponse = lambda r: response.append(r)

        protocol.requestReceived("GET", "/", [], "")
        # We don't assert anything on the body of the response; if you're
        # feeling ambitious you can include the text of the traceback in your
        # response:
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].code, 500)
        # You should log the error using twisted.python.log.err(). This makes
        # sure the logged error doesn't cause the test to fail:
        excs = self.flushLoggedErrors(RuntimeError)
        # And this asserts that you logged it, i.e. that there was one
        # RuntimeError logged:
        self.assertEqual(len(excs), 1)

    def test_12_handlerReturnsDeferred(self):
        """
        If the handler returns a Deferred that fires with (code, body,
        headers), L{HTTP.requestReceived} writes it as a response using
        L{HTTP._writeResponse}.
        """
        # Handler that returns eventual result:
        result = defer.Deferred()
        def handler(method, path, headers, body):
            return result

        protocol = HTTP(handler, reactor=task.Clock())
        response = []
        protocol._writeResponse = lambda r: response.append(r)

        protocol.requestReceived("GET", "/", [], "")
        # Deferred hasn't fired yet, so no response is sent yet:
        self.assertEqual(len(response), 0)
        # Now we fire the Deferred, and response should be written:
        result.callback(Response(200, "response", {"key": "value"}))
        self.assertResponsesEqual(response[0],
                                  Response(200, "response", {"key": "value"}))

    def test_13_handlerReturnsBadDeferred(self):
        """
        If the handler returns a Deferred that fires with something that isn't
        a good response, L{HTTP.requestReceived} write a 500 response code
        using L{HTTP._writeResponse} and logs the exception.
        """
        # Handler that returns eventual result:
        result = defer.Deferred()
        def handler(method, path, headers, body):
            return result

        protocol = HTTP(handler, reactor=task.Clock())
        response = []
        protocol._writeResponse = lambda r: response.append(r)

        protocol.requestReceived("GET", "/", [], "")
        # Deferred hasn't fired yet, so no response is sent yet:
        self.assertEqual(len(response), 0)
        # Now we fire the Deferred with something that isn't a valid handler
        # response:
        result.callback("lalalal")
        # 500 response code:
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].code, 500)
        # The error was logged using twisted.python.log.err():
        excs = self.flushLoggedErrors()
        self.assertEqual(len(excs), 1)

    def test_14_handlerReturnsDeferredWithFailure(self):
        """
        If the handler returns a Deferred that fires with a failure,
        L{HTTP.requestReceived} writes a 500 response code using
        L{HTTP._writeResponse} and logs the exception.
        """
        # Handler that returns eventual result:
        result = defer.Deferred()
        def handler(method, path, headers, body):
            return result

        protocol = HTTP(handler, reactor=task.Clock())
        response = []
        protocol._writeResponse = lambda r: response.append(r)

        protocol.requestReceived("GET", "/", [], "")
        # Deferred hasn't fired yet, so no response is sent yet:
        self.assertEqual(len(response), 0)
        # Now we fire the Deferred with an exception:
        result.errback(ZeroDivisionError())

        # 500 response code:
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].code, 500)
        # The error was logged using twisted.python.log.err():
        excs = self.flushLoggedErrors(ZeroDivisionError)
        self.assertEqual(len(excs), 1)

    def test_15_timeout(self):
        """
        If the L{HTTP} protocol takes more than 60 seconds to receive the
        request, it will close the connection by calling transport.abortConnection().
        """
        transport = AbortableTransport()
        fakeReactor = task.Clock()
        protocol = HTTP(None, reactor=fakeReactor)

        protocol.makeConnection(transport)
        protocol.dataReceived('GET')
        self.assertFalse(transport.aborting)

        # Wait 60 seconds:
        fakeReactor.advance(60)
        self.assertTrue(transport.aborting)

    def test_16_noTimeoutInResponse(self):
        """
        Once the full request has been received, the L{HTTP} protocol will not
        time out, i.e. will not close the connection even if it sits more than
        60 seconds without receiving bytes.

        This is because at this point it's the server's responsibility to
        reply, which may take a while, and in the interim the server doesn't
        expect any bytes from the client so lack of data from client does not
        indicate a problem.
        """
        transport = AbortableTransport()
        fakeReactor = task.Clock()
        # Handler that takes forever to return, while still keeping reference
        # to the Deferred. If it didn't do the latter, it would get GC'ed,
        # which can cause unexpected things like a GeneratorExit exception in
        # an inlineCallbacks-decorated handler.
        handlerResult = defer.Deferred()
        def handler(*args):
            return handlerResult

        protocol = HTTP(handler, reactor=fakeReactor)

        protocol.makeConnection(transport)
        protocol.dataReceived('GET / HTTP/1.1\r\n\r\n')
        self.assertFalse(transport.aborting)

        # Wait 60 seconds:
        fakeReactor.advance(60)
        self.assertFalse(transport.aborting)

    def test_17_demo(self):
        """
        If you've got tests 1-16 passing, you should be able to run demo2.py.
        """
    test_17_demo.skip = "This needs to be run manually."


    def test_18_contentLength(self):
        """
        If the HTTP request includes a 'content-length' header, the value
        indicates the number of bytes of the request body, which will get
        passed as the fourth argument to the requestReceived.
        """
        protocol = HTTP(None, reactor=task.Clock())
        received = []
        protocol.requestReceived = lambda *args: received.append(args)
        protocol.makeConnection(AbortableTransport())

        protocol.dataReceived("GET /foo/bar HTTP/1.1\r\n")
        protocol.dataReceived("Content-Length: 10\r\n")
        protocol.dataReceived("\r\n")
        protocol.dataReceived("abcde")
        self.assertEqual(received, [])
        protocol.dataReceived("fghij")
        self.assertEqual(
            received,
            [("GET", "/foo/bar", {"Content-Length": "10"}, "abcdefghij")])

    def test_19_requestBodyToHandler(self):
        """
        If the HTTP request includes a body, it is passed to the handler
        function.
        """
        result = []
        def handler(method, path, headers, body):
            result.append(body)
            return Response(200, "hello", {})

        protocol = HTTP(handler, reactor=task.Clock())
        response = []
        protocol._writeResponse = lambda r: response.append(r)

        protocol.requestReceived("GET", "/", {}, "the body")
        self.assertEqual(result, ["the body"])

    @defer.inlineCallbacks
    def test_20_endToEnd(self):
        """
        The HTTP implementation is compatible with a real HTTP client, in so
        far as it can reply to a simple HTTP POST.
        """
        from twisted.web.client import getPage

        # Handler that returns the request body as the body of the response:
        def handler(method, path, headers, body):
            self.assertEqual(method, "POST")
            return Response(200, body, {})

        port = reactor.listenTCP(0, HTTPFactory(handler), interface="127.0.0.1")
        self.addCleanup(port.stopListening)
        portNumber = port.getHost().port
        url = "http://127.0.0.1:%d/" % (portNumber,)

        result = yield getPage(url, method="POST", postdata="Some data")
        self.assertEqual(result, "Some data")
