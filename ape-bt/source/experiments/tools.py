import time

from twisted.internet import reactor, defer


def sleep(timeout):
    df = defer.Deferred()
    start_time = time.time()

    def callback():
        dt = time.time() - start_time
        df.callback(dt)

    reactor.callLater(timeout, callback)
    return df


