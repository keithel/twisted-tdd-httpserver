This lab will have you implement a simple HTTP server, and then a client. Your
initial goal is to make all the tests pass, and when you're done you'll have a
basic toy HTTP server.

You can run the tests using the trial command-line tool:

    $ trial toyhttp.tests.test_server

Or you can run an individual test:

    $ trial toyhttp.tests.test_server.Tests01_Protocol.test_01_writeResponse

On Windows you'd run trial like this, in CMD.EXE:

    $ c:\python27\python.exe c:\python27\scripts\trial.py

You should try to make the tests pass one by one, in order, rather than trying
to make all of them pass at once.

Once you've finished the server, you get to work on the HTTP client. For the
client no tests are provided; it's up to you to write the tests. See
`toyhttp/client.py` for some hints.


=== Solution notes ===

  1. You'll probably want to use twisted.protocols.basic.LineReceiver. Note
     that the this protocol requires a transport to be connected (a fake one
     is fine) even to test dataReceived.

  2. Useful reading material:
     * TCP servers: http://twistedmatrix.com/documents/current/core/howto/servers.html
     * Unit tests: http://twistedmatrix.com/documents/current/core/howto/trial.html
     * Deferreds: http://twistedmatrix.com/documents/current/core/howto/defer.html
     * Logging: http://twistedmatrix.com/documents/current/core/howto/logging.html
     * Scheduling and Timeouts: http://twistedmatrix.com/documents/current/core/howto/time.html
     * TCP clients: http://twistedmatrix.com/documents/current/core/howto/clients.html


=== The HTTP Protocol ===

To get an overview of the HTTP protocol, see
http://www.jmarshall.com/easy/http/, and then the HTTP RFC. Short version: a
HTTP client, e.g. a browser, sends a request to the server. The server replies
with a response. Requests look something like this -- they have a method, a
path, some headers and sometimes a body (not shown in this example). All lines
end with the two special characters '\r\n'; an empty line indicates the end of
the structured part of the HTTP request, and the start of the body, if it has
one.

    GET /path HTTP/1.1\r\n
    User-Agent: Mozilla/12.0\r\n
    \r\n

And responses look like this -- they have a response code (200), a meaningless
text version of the response code (OK), some headers, and usually a body, in
this case saying "Hello world!". Notice there's no '\r\n' at the end of the
response body, since the content-length header tells the browser exactly how
many bytes to expect.

    HTTP/1.1 200 OK\r\n
    Content-Length: 12\r\n
    Content-Type: text/plain\r\n
    \r\n
    Hello world!

Requests can also have bodies (and notice that headers are case insensitive):

    POST /path HTTP/1.1\r\n
    content-length: 3\r\n
    \r\n
    ABC
