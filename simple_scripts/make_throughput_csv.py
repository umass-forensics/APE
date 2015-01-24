#!/usr/bin/env python2.7

import sys
import os
from traceutils.utilities import parse_path


trials_idx = 0
trials_map = {}

for filein in sys.argv[1:]:
    with open(filein, 'r') as f:
        lines = f.readlines()

    old_header = ','.join(lines[0].strip().split(',')[1:]).replace('-', 's_').replace('+', 'r_')

    print 'trial,clientid,clienttype,' + old_header

    #skip the first line
    for line in lines[1:]:
        key = ''.join(line.split('_')[:-1])
        if key not in trials_map:
            trials_map[key] = str(trials_idx)
            trials_idx += 1

        trial = trials_map[key]

        parts = line.strip().split(',')
        path = parts[0]
        rest = parts[1:]

        clientid, clienttype = parse_path(path)

        print ','.join([trial, clientid, clienttype] + rest)

