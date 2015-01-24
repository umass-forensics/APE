# About

This repository contains code, experiments, and writing related to my protocol
analysis work.

# Directory Info

*ape* directory. Contains all sorts of fun code needed to run Ape. 

*experiments* directory. This directory contains the scripts and results for
related experiments and tests. Subdirectories should be named descriptively and
contain README files describing information about the experiments such as its
purpose and how to run it.

Right now I am in the process reorganizing this directory and changing how we
store the large trace files.

*ape-bt* directory. This directory is a submodule of a separate git
repository. It contains a BitTorrent tester based on a modified version of the
AutonomoTorrent client.

*synoptic*: The synoptic modeling tool. I use this to generate protocol models
from log files. This directory is current a separate mercurial repository (since
that is what the project designers used).

*synoptic-out*: A temporary storage directory, ignored by git, that I use to
store intermediate synoptic results. 

# Setting up the environment

First clone the main repository from Github. This will take a few
minutes...okay, a bit more than a few.

```bash
git clone git@github.com:umass-forensics/APE.git
```

Let's not forget about Synoptic, which is actually a mercurial repository.  

```bash
hg clone https://code.google.com/p/synoptic/ synoptic
```

We need to build synoptic:

```bash
cd synoptic
ant
```
Once inside of the vagrant VM we can generate some traces using a
command like:

    cd /ape/
    python __main__.py \
        -m /args/vargs_synoptic.txt \
        -t /args/vargs_apebt.txt \
        -u /args/vargs_utorrent.txt \ 
        -o /experiments/utorrent/traces_explore_nsbasicstartv2_5_2 \
        --num_traces_periter=5 \
        --num_iteration=2 \
        -i /experiments/utorrent/initial_varied.dot

Use `python __main__.py -h` to get an overview of all of the options.

If both the tester and target seem to be running fine, but you get the 'Failed
to connect' error, you might have a problem with your firewall settings on your
router.
