#!/usr/bin/python

"""
Run a trivial HTTP server at <http://127.0.0.1:8080/>.

This requires tests 1-13 of test_server.py to be passing; it demonstrates that
handlers can return Deferreds by doing a DNS lookup in response to a
form. Multiple DNS requests can run in parallel.
"""

import sys, urlparse

from twisted.internet import reactor, defer
from twisted.python import log
from toyhttp import server

FORM = """\
<html>
<body>
<p>%(message)s</p>

<form action="/resolve">
  Hostname: <input name="hostname" value="%(hostname)s"> <input type="submit">
</form>
<body>
</html>
"""

def renderResult(message, hostname):
    result = FORM % {"message": message, "hostname": hostname}
    return server.Response(200, result, {"content-type": "text/html"})


@defer.inlineCallbacks
def resolve(parsedPath):
    arguments = urlparse.parse_qs(parsedPath.query)
    hostname = arguments["hostname"][0]
    try:
        ip = yield reactor.resolve(hostname)
    except Exception, e:
        message = str(e)
    else:
        message = "<b>%s</b> has IP address <b>%s</b>." % (hostname, ip)

    # This is how inlineCallbacks returns a result:
    defer.returnValue(renderResult(message, hostname))


def dnsResolver(method, path, headers, body):
    """
    A HTTP handler that does DNS lookups.
    """
    parsedPath = urlparse.urlparse(path)
    if parsedPath.path == "/":
        return renderResult("Please enter a hostname, e.g. www.google.com:", "")
    elif parsedPath.path == "/resolve":
        return resolve(parsedPath)
    else:
        return server.Response(404, "Bad path.", {"content-type": "text/plain"})


if __name__ == '__main__':
    print "Point your browser at http://localhost:8080/"
    log.startLogging(sys.stdout)
    reactor.listenTCP(8080, server.HTTPFactory(dnsResolver))
    reactor.run()
