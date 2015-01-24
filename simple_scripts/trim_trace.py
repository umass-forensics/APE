__author__ = 'wallsr'
import datetime
from optparse import OptionParser

def main():
    usage = 'usage: %prog [options] trace0'
    parser = OptionParser(usage=usage)

    parser.add_option('-s', dest='str_start')
    parser.add_option('-e', dest='str_end')

    options, args = parser.parse_args()

    #TODO
    start = datetime.datetime.strptime(options.str_start,
                                       '%Y-%m-%d %H:%M:%S.%f')

    end = datetime.datetime.strptime(options.str_end,
                                       '%Y-%m-%d %H:%M:%S.%f')

    with open(args[0], 'r') as f:
        lines = f.readlines()

    for line in lines:
        try:
            timestamp = datetime.datetime.strptime(line[0:26],
                                               '%Y-%m-%d %H:%M:%S.%f')
        except:
            continue

        if start <= timestamp <= end:
            print line,




    pass

if __name__ == '__main__':
    main()