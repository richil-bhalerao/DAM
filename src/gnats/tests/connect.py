#!/usr/local/bin/python
"""
Simple program that connects to gnatsd and fetches db metadata.

Logs all protocol conversation to STDERR, so you can see how things are going.

Dirk Bergstrom, dirk@juniper.net, 2008-06-15

Copyright (c) 2008, Juniper Networks, Inc.
All rights reserved.
"""

import logging
from optparse import OptionParser
import os

gnats_path = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]
if gnats_path not in os.sys.path:
    os.sys.path.append(gnats_path)
import gnats

if __name__ == '__main__':
    parser = OptionParser(usage="usage: %prog [options]\nConnect to a GNATS db.")
    parser.add_option('-p', '--port', dest='port', action="store",
                      help='Port to connect to, defaults to "%default".',
                      default=1529)
    parser.add_option('-H', '--host', dest='host', action="store",
                      help='Host to connect to, defaults to "%default".',
                      default='localhost')
    parser.add_option('-d', '--database', dest='db', action="store",
                      help='Database to connect to, defaults to "%default".',
                      default='default')
    parser.add_option('-q', '--quiet', dest='quiet', action="store_true",
                      help='Emit no output', default=False)
    options, args = parser.parse_args()

    if options.quiet:
        logging.basicConfig(level=logging.FATAL)
    else:
        logging.basicConfig(level=logging.DEBUG)

    db = gnats.Server(options.host, port=options.port).get_database(options.db)

    if not options.quiet:
        print db
#        for f in db.list_fields():
#            print f