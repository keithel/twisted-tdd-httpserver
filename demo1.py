#!/usr/bin/python

"""
Run a trivial HTTP server at <http://127.0.0.1:8080/>.

This requires tests 1-8 of test_server.py to be passing. Try different URLs in
your browser, e.g. <http://127.0.0.1:8080/foo?x=y>.
"""

import sys

from twisted.internet import reactor
from twisted.python import log
from toyhttp import server


class Handler(object):
    """
    Handle HTTP requests; provide a counter and some debugging info.
    """

    def __init__(self):
        self.counter = 0

    def __call__(self, method, path, headers):
        result = "You requested %r with method %r.\n\n"  % (path, method)
        result += "Your headers:\n"
        for header in headers:
            result += header + "\n"
        return server.Response(200, result, {"content-type": "text/plain"})



if __name__ == '__main__':
    log.startLogging(sys.stdout)
    reactor.listenTCP(8080, server.HTTPFactory(Handler()))
    reactor.run()
