
import tools
import time
from twisted.internet import defer, reactor

@defer.inlineCallbacks
def hisleep():
    for x in xrange(30):
        print 'hi!', x
        yield tools.sleep(1.0)

@defer.inlineCallbacks
def no():
    for x in xrange(4):
        print 'no!', x
        yield tools.sleep(3.0)

hisleep()
no()

reactor.run()
