#!/usr/bin/env python2.7
import datetime
import os
import sys

from optparse import OptionParser


def truncate_lines(traces, verbose=False):
    #Find the shortest trace (by time)
    cutoff = None

    for name, trace in traces:
        last = trace[-1][0:26]
        end = datetime.datetime.strptime(last, '%Y-%m-%d %H:%M:%S.%f')

        if cutoff is None or end < cutoff:
            cutoff = end

    if verbose:
        print 'Truncating at: %s', str(cutoff)

    traces_new = []

    for name, trace in traces:
        index = len(trace)
        for x in xrange(len(trace)):
            line = trace[x]
            timestamp = datetime.datetime.strptime(line[0:26],
                                                   '%Y-%m-%d %H:%M:%S.%f')
            if timestamp > cutoff:
                index = x
                if verbose:
                    print 'Truncating %s' % name
                break

        traces_new.append((name, trace[0:index]))

    return traces_new




def grab_piece_lines(tracefile, verbose=False):
    with open(tracefile, 'r') as f:
        lines = f.readlines()
        #only grab the lines with a received piece message
        lines = [l for l in lines if '+piece' in l]

        if len(lines) == 0:
            if verbose:
                print 'No piece messages found in trace'
            return []
        else:
            return lines


def calculate_throughput(lines, verbose=False):
    if lines is None or len(lines) <= 1:
        if verbose:
            print 'No piece messages found in trace'
        return 0.0

    first = lines[0][0:26]
    last = lines[-1][0:26]


    start = datetime.datetime.strptime(first, '%Y-%m-%d %H:%M:%S.%f')
    end = datetime.datetime.strptime(last, '%Y-%m-%d %H:%M:%S.%f')
    seconds = (end - start).total_seconds()

    if seconds == 0:
        seconds = 1

    pieces_per_second = 1.0 * len(lines) / seconds
    bits_per_piece = 16384*8
    kbits = bits_per_piece / 1024.0
    throughput = kbits * pieces_per_second

    if verbose:
        print first
        print last
        print 'Seconds: %f' %seconds
        print 'Pieces: %d' %len(lines)
        print 'Pieces/second %f' %pieces_per_second
        print 'Throughput %f Kbps' % throughput

    return throughput


def main():
    usage = 'usage: %prog [options] trace0 trace1 ...'
    parser = OptionParser(usage=usage)

    parser.add_option('-t', '--truncate', action='store_true',
                      dest='truncate', default=False)
    parser.add_option('-v', '--verbose', action='store_true',
                      dest='verbose', default=False)

    options, args = parser.parse_args()

    if not options.truncate:
        for f in args:
            lines = grab_piece_lines(f, options.verbose)
            print '%s,%f,%d' % (f, calculate_throughput(lines), len(lines))
    else:
        traces = [(f, grab_piece_lines(f))
                  for f in args
                  if grab_piece_lines(f, options.verbose) is not None]

        traces = truncate_lines(traces, options.verbose)

        for f, lines in traces:
            print '%s,%f,%d' % (f, calculate_throughput(lines, options.verbose), len(lines))


if __name__ == '__main__':
    main()