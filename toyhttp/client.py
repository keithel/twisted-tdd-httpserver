"""
A toy HTTP client implementation.

At this point you should know enough to manage on your own: you get to
write both tests and code!

Some suggestions:

* Since much of the byte-processing code in a client and server is similar
  (HTTP requests and responses are mostly the same, except for the first
  line), you might want to share the implementations. That is, refactor the
  server protocol to rely on a parsing and rendering protocol base class that
  can be specialized to support both client and server protocols. The base
  protocol would know how to parse incoming data into a first line, a
  dictionary of headers, and a body. It would also know how to write out a
  first line, a dictionary of headers and a body to a transport.

* ClientCreator or endpoints will make your implementation simpler.
"""

def getPage(url, method="GET", headers={}, body=None):
    """
    Send a HTTP request to the given url, using the given method, headers and
    optional body.

    @param url: A string, the URL to connect to, e.g.
        'http://www.example.com/foo'.

    @param method: The method to send to the server, e.g. 'GET' or 'POST'.

    @param headers: A dictionary mapping header keys to values,
        e.g. {'user-agent': 'mydemo'}.

    @param body: Optional, the request body as bytes. If included, a
        Content-Length header will be added automatically.

    @return: A Deferred that fires with a Response object on success, or fires
       with an appropriate error.
    """
    raise NotImplementedError()
