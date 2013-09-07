"""
GNATS Protocol Library

This package provides classes and methods for interaction with GNU GNATS
bug tracking systems.

If you want to query, read, create or edit PRs, use the get_database_handle
function to obtain a DatabaseHandle object, and use its methods directly.

If you need to work with database metadata, such as field names and values,
required fields, etc., use the get_database function to obtain a Database
object.  To work with PRs, use that object's get_handle method to obtain
a DatabaseHandle object.

The library transparently handles loading and caching of server and database
metadata, controllable via the variables discussed below.  The get_database and
get_database_handle convenience methods also cache Database and Server objects.

All data from gnatsd is supplied in unicode, and should be encodable as
ISO-8859-1.

Example
========

import os, gnats

host = 'gnats.juniper.net'
db = 'default'
username = os.getlogin()

# The columns we want, and the query
columns = ['number', 'category', 'synopsis']
expr = 'state!="closed" & responsible=="%s"' % username

# Get a database object, which holds the metadata (field names, etc.)
db_obj = gnats.get_database(host, db)
# Get a db handle, a connection to the server
db_handle = db_obj.get_handle(username, passwd='*')

try:
   # Run the query, which returns a list of lists
   prs = db_handle.query(expr, columns, sort=(('synopsis', 'desc'),))
except gnats.GnatsException, err:
   print "Error in query: %s" % err.message

print "User %s's PRs in database %s" % (username, db_obj.description)
print "Columns:"
for col in columns:
    fld = db_obj.fields[col]
    print "%s: %s" % (fld.name, fld.description)
for pr in prs:
    print "%s - %s - %s" % (pr[0], pr[1], pr[2])

Global Package Variables
========================

'metadata_level'
Defaults to FULL_METADATA
Controls the amount of database metadata loaded from gnatsd when a Database
object is instantiated (and re-loaded when it is determined to be stale).  If
you are building a full-featured GNATS client, or need to know all enum values,
use FULL_METADATA.  If you just want to interact with gnatsd, NO_ENUM_METADATA
is a good choice.  The difference between the various levels is 0.5-2 seconds
per load; the variation in load times at FULL_METADATA level can be as much
as 2 seconds, depending on server load, so monkeying with this setting may
not make a big difference.

The following values are valid:
  FULL_METADATA: Load all metadata.  All methods and properties should work.
  NO_ENUM_METADATA: Load everything except enum field values and subfield
names.  This saves a significant amount of time if there are enum fields
with thousands of values.  However, Database.validate_* methods will
raise an exception.  The load_enum_values method can be called on individual
EnumField instances, but the library will wipe out the values when a metadata
refresh is automatically triggered.
  MINIMAL_METADATA: Load field name and type information sufficient to
satisfy the methods in DatabaseHandle.  This level is only marginally faster
than NO_ENUM_METADATA. The following methods and data are affected:
    - Database.validate_* methods will raise an exception.
    - EnumField.list_values will raise.
    - Database.initial_entry_fields will be empty.
  NO_METADATA: No metadata will be loaded.  Do not use this value unless
you have read and understood the code in database.py.  It's here for
the advanced user, and for the sake of completeness.

'refresh_metadata_automatically'
Defaults to True
When True, Database instances will check the currency of their metadata on
every call to get_handle(), and if the server indicates that its configuration
has changed, the metadata will be reloaded (which takes 1-4 seconds,
depending on metadata_level and server load).  When False, the user should call
Database.update_metadata() periodically to ensure that cached data is still
valid.  Leave it True unless you find a compelling reason to set it to False.

The following flags control "advanced" properties of the library.  Do not
mess with them unless you know what you're doing.

'allow_cmd_control_chars'
Defaults to False
Most control characters (except for tab, esc, and the four separators used in
query results parsing) are stripped out of protocol commands before they are
sent to the server.  This cuts down on "invisible" errors, and helps guard
against protocol injection attacks.  When this flag is set, only newlines are
stripped (as they will definitely cause failure).  Use only if truly needed.

'protocol_debug'
Defaults to False
Dumps debug info about low-level protocol parsing (probably much more output
than you want).

Administrivia
=============

This file may be found at cvs/juniper/sw-tools/src/gnatatui/gnats/__init__.py

Dirk Bergstrom, dirk@juniper.net, 2008-04-17

Copyright (c) 2008-2009, Juniper Networks, Inc.
All rights reserved.
"""

# API docs can be generated via epydoc with:
#    epydoc gnats/*.py

import codes

# GNATS data should be in this encoding (we hope...)
ENCODING = 'iso-8859-1'
# What we do when we encounter an encoding error:
# strict == raise UnicodeEncodeError
# replace == stick in an error character
# ignore == leave out the offending bytes
ENCODING_ERROR = 'replace'

# Controls loading of db metadata (see package docstring)
FULL_METADATA = (3, 'FULL_METADATA')
NO_ENUM_METADATA = (2, 'NO_ENUM_METADATA')
MINIMAL_METADATA = (1, 'MINIMAL_METADATA')
NO_METADATA = (0, 'NO_METADATA') # This will almost certainly cause errors
metadata_level = FULL_METADATA

# Controls automatic db metadata re-loading
refresh_metadata_automatically = True

# Don't strip (most) ctrl chars from protocol commands
allow_cmd_control_chars = False

# Print debug info during low-level protocol parsing.
protocol_debug = False

class GnatsException(Exception):
    """ General GNATS errors """

    def __init__(self, message, code=None):
        Exception.__init__(self, message)
        self.message = message
        self.code = code

class GnatsAccessException(GnatsException):
    """ Access denied by GNATS, or user lacks sufficient privileges. """

class GnatsNetworkException(GnatsException):
    """ Network and protocol parsing errors """

class PRNotFoundException(GnatsException):
    """ The requested PR was not found. """

class InvalidFieldNameException(GnatsException):
    """ A non-existent field name was given. """

class LastModifiedTimeException(GnatsException):
    """ The PR has been modified since the user started editing it. """

    def __init__(self, message, old_time=None, new_time=None):
        GnatsException.__init__(self, message)
        self.message = message
        self.old_time = old_time
        self.new_time = new_time


from database import Database, DatabaseHandle, Field, EnumField
from server import Server, ServerConnection

_server_cache = {}

def get_database(host, dbname, port=codes.DEFAULT_PORT):
    """ Get a Database object for database dbname on host.

    Convenience method.
    """
    try:
        server = _server_cache['%s-%s' % (host, port)]
    except KeyError:
        server = Server(host, port=port)
        _server_cache['%s-%s' % (host, port)] = server
    return server.get_database(dbname)

def get_database_handle(host, dbname, username, passwd=None,
                        port=codes.DEFAULT_PORT):
    """ Get a DatabaseHandle object for database dbname on host.

    Convenience method.
    """
    return get_database(host, dbname, port=port).\
               get_handle(username, passwd=passwd)
