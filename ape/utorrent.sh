#!/usr/bin/env bash

echo date

python __main__.py -m /args/vargs_synoptic.txt \
    -t /args/vargs_apebt.txt \
    -u /args/vargs_utorrent.txt \
    -i /experiments/autonomo/ns_basic.dot \
    -o /experiments/utorrent/explore_nsbasicstart_10_10 \
    --num_traces_periter 10 \
    --num_iteration 10

echo date

python __main__.py -m /args/vargs_synoptic.txt \
    -t /args/vargs_apebt.txt \
    -u /args/vargs_utorrent.txt \
    -i /experiments/autonomo/ns_basic.dot \
    -o /experiments/utorrent/explore_nsbasicstart_25_4 \
    --num_traces_periter 25 \
    --num_iteration 4

echo date

python __main__.py -m /args/vargs_synoptic.txt \
    -t /args/vargs_apebt.txt \
    -u /args/vargs_utorrent.txt \
    -i /experiments/autonomo/ns_basic.dot \
    -o /experiments/utorrent/explore_nsbasicstart_300_1 \
    --num_traces_periter 300 \
    --num_iteration 1

echo date

python __main__.py -m /args/vargs_synoptic.txt \
    -t /args/vargs_apebt.txt \
    -u /args/vargs_utorrent.txt \
    -i /experiments/autonomo/ns_basic.dot \
    -o /experiments/utorrent/explore_nsbasicstart_50_6 \
    --num_traces_periter 50 \
    --num_iteration 6

