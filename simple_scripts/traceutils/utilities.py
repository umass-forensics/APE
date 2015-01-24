__author__ = 'wallsr'

import datetime
import re


regex_eventline = re.compile(r' 2d[45].*, (?P<event>[\-\+]\w+)')


def get_time(lines, null_failures=False):
    times = []

    for line in lines:
        try:
            timestr = line[0:26]
            time = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S.%f')
            times.append(time)
        except:
            if null_failures:
                times.append(None)

    return times


def parse_path(path):
    #Assume paths look like
    #throughput_azureus_tmp/throughput/proc_0_apebt_evil4.txt

    if path.startswith('./'):
        path = path[2:]

    parts = path.split('/')
    clientid = parts[2].split('_')[3].replace('.txt', '')
    clienttype = clientid[:4]

    return clientid, clienttype


def calculate_throughput(handshake_lines, request_lines, piece_lines, all_lines, verbose=False):
    """
    Start time from the handshake, and end when all requests are satisfied or
    at the end of the trace if they aren't all satisfied.
    """
    if piece_lines is None or len(piece_lines) <= 1:
        if verbose:
            print 'No piece messages found in trace'
        return 0.0

    #Time of handshake
    first = handshake_lines[0][0:26]
    start = datetime.datetime.strptime(first, '%Y-%m-%d %H:%M:%S.%f')

    #Time of trial end. Assuming the last line has a timestamp
    last = all_lines[-1][0:26]
    end = datetime.datetime.strptime(last, '%Y-%m-%d %H:%M:%S.%f')

    #Check if all request were satisfied. estimate by checking if we
    #received a piece after the last request.
    time_of_last_request = datetime.datetime.strptime(request_lines[-1][0:26],
                                                      '%Y-%m-%d %H:%M:%S.%f')
    time_of_last_piece = datetime.datetime.strptime(piece_lines[-1][0:26],
                                                    '%Y-%m-%d %H:%M:%S.%f')

    if time_of_last_piece > time_of_last_request:
        end = time_of_last_piece

    seconds = (end - start).total_seconds()

    if seconds == 0:
        seconds = 1

    pieces_per_second = 1.0 * len(piece_lines) / seconds
    bits_per_piece = 16384*8
    kbits = bits_per_piece / 1024.0
    throughput = kbits * pieces_per_second

    if verbose:
        print first
        print last
        print 'Seconds: %f' %seconds
        print 'Pieces: %d' %len(piece_lines)
        print 'Pieces/second %f' %pieces_per_second
        print 'Throughput %f Kbps' % throughput

    return throughput


def get_unique_events(lines):
    events = {}
    for line in lines:
        res = regex_eventline.search(line)

        if res is not None and res.groups() is not None:
            event = res.group('event')

            if event not in events:
                events[event] = []

            events[event].append(line)

    return events
