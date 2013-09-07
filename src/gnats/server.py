"""
GNATS Server and ServerConnection

Dirk Bergstrom, dirk@juniper.net, 2008-04-17

Copyright (c) 2008-2009, Juniper Networks, Inc.
All rights reserved.
"""
import socket
import time
import re
import logging

import gnats
import codes
from gnats import GnatsAccessException, GnatsException, GnatsNetworkException
from gnats import Database

_LOG = logging.getLogger('server')

# Define global variable to re-use the same gnatsd connection.
connection = None

class Server(object):
    """ A GNATS server, which may host multiple Databases.

    Use the get_connection method to obtain a ServerConnection, which can be
    used for low-level interaction with the gnatsd server.  In most cases you
    are better off using Database and DatabaseHandle.

    This class is mostly used internally.
    """

    # Number of second to cache database list
    CACHE_TIME = 600

    def __init__(self, host, port=codes.DEFAULT_PORT, cache_time=CACHE_TIME):
        self.host = host
        self.port = int(port)
        self._database_names = []
        self._databases = {}
        self._dbls_time = 0
        self._dbusers = {} # hash of tuples of (username, passwd)
        self.cache_time = cache_time
        self.gnatsd_version = 'UNKNOWN'

    def __str__(self):
        return "GNATS %s Server at %s:%s" % \
            (self.gnatsd_version, self.host, self.port)

    def __repr__(self):
        return "<%s>" % self.__str__()

    def list_databases(self, conn=None):
        """ List the databases on this server. """
        if conn is not None or time.time() - self._dbls_time > self.cache_time:
            conn = self.get_connection(conn)
            global connection
            connection = conn
            self._database_names = conn.dbls()
            self._dbls_time = time.time()
        return self._database_names

    def _validate_conn(self, conn):
        """ Return the supplied connection if it is valid for this server,
        otherwise raise GnatsException.
        """
        if conn.server != self:
            raise GnatsException("Supplied connection not for this server.")
        return conn

    def get_connection(self, conn=None):
        """ Return a new connection, or the one passed in.

        Used to avoid creating new connections needlessly.
        """
        if conn is not None:
            return self._validate_conn(conn)
        else:
            conn = ServerConnection(self)
            self.gnatsd_version = conn.gnatsd_version
            return conn

    def get_database_handle(self, dbname, username, passwd=None, conn=None):
        """ Return a connection to the named database. """
        return self.get_database(dbname, conn).get_handle(username, passwd, conn)

    def get_database(self, dbname, conn=None):
        """ Get a Database object.

        If a connection is supplied, it will be used to fetch the db metadata.
        """
        global connection
        conn = connection
        if not dbname in self._database_names:
            self._dbls_time = 0
            self.list_databases(conn)
            if not dbname in self._database_names:
                raise GnatsException("Database '%s' not found on server %s:%s" %
                                     (dbname, self.host, self.port))
        if self._databases.has_key(dbname):
            return self._databases[dbname]
        else:
            db = Database(self, dbname, self.get_connection(conn))
            self._databases[dbname] = db
            return db

    def dbuser(self, dbname):
        """ Return a username password tuple that can log into the given
        database and retrieve metadata.
        """
        return self._dbusers.get(dbname, ('gnatatui','*'))


class ServerConnection(object):
    """ A connection to a GNATS server.

    This class is normally not directly employed by the user, instead a
    DatabaseHandle instance, and its high-level methods should be used.
    The command() method and the low-level protocol commands are primarily
    used internally, but made available for the brave user.

    If you pass in a ServerConnection object to the constructor, the socket
    (and thus connection to gnatsd) will be re-used.

    Set strict_protocol to False to "work through" unknown reply state values.
    """
    # TODO Consider using raw socket send/recv calls, instead of makefile.
    # Profiling shows that half the time required for reading data is spent
    # in socket._fileobject.readline() (almost half of that on data.find('\n')).
    _SERVER_VERSION_RE = re.compile(r'.*GNATS server (.*) ready.*')
    def __init__(self, server, conn=None, strict_protocol=True):
        self.strict_protocol = strict_protocol
        self.server = server
        if conn is not None:
            # copy the socket from the supplied connection.  get_connect() will
            # validate the supplied connection and return it.
            self._sock = server.get_connection(conn)._sock
            self._sfile = conn._sfile
            self.gnatsd_version = conn.gnatsd_version
            # XXX??? Should we do something to check the viability of the conn?
        else:
            # Make a new socket connection
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self._sock.connect((server.host, server.port))
                self._sfile = self._sock.makefile()
                mo = self._SERVER_VERSION_RE.match(self._get_reply(False)[0])
            except (socket.error, IOError):
                raise GnatsNetworkException("Error connecting to gnatsd at "
                    "%s port %s" % (server.host, server.port))
            if mo:
                self.gnatsd_version = mo.group(1)
            else:
                self.gnatsd_version = 'UNKNOWN VERSION'

    def __str__(self):
        return "ServerConnection for %s" % self.server

    def __repr__(self):
        return "<%s>" % self.__str__()

    # Protocol conversation methods

    _CTRL_STRIP_RE = re.compile(r'[\x01-\x08\x0a-\x1a]')
    def command(self, cmd, parse=False):
        """ Send the given protocol command and arguments to gnatsd,
        return the output as a list of lines.

        Most control characters are stripped out of the command before it
        is sent.  See package docs on 'allow_cmd_control_chars'.
        """
        if gnats.allow_cmd_control_chars:
            fixed_cmd = cmd.replace('\n', ' ')
        else:
            fixed_cmd = self._CTRL_STRIP_RE.sub(' ', cmd)
        fixed_cmd = fixed_cmd.encode(gnats.ENCODING, gnats.ENCODING_ERROR)
        _LOG.debug("Sending command '%s'", fixed_cmd)
        try:
            self._sfile.write(fixed_cmd)
            self._sfile.write("\n")
            self._sfile.flush()
        except (IOError, socket.error):
            raise GnatsNetworkException('Error sending command "%s" to '
                    'gnatsd at %s port %s' %
                    (fixed_cmd, self.server.host, self.server.port))
        return self._get_reply(parse)

    _SERVER_REPLY_RE = re.compile(r'(\d+)([- ]?)(.*?)\s*$')
    def _server_reply(self):
        """ Read and parse protocol reply lines from the server.

        Returns (state, text, type, raw_reply).
        """
        try:
            raw_reply = unicode(self._sfile.readline(), gnats.ENCODING)
        except (IOError, socket.error):
            raise GnatsNetworkException('Error reading reply from '
                'gnatsd at %s port %s' % (self.server.host, self.server.port))
        if gnats.protocol_debug:
            # Log line w/o trailing newline
            _LOG.debug("Reply: %s", raw_reply[:-1])
        mo = self._SERVER_REPLY_RE.match(raw_reply)
        if mo:
            state = mo.group(1)
            text = mo.group(3)
            if mo.group(2) == '-':
                rtype = codes.REPLY_CONT
            else:
                if mo.group(2) != ' ':
                    raise GnatsNetworkException("Bad reply type from server " +
                                                "(neither ' ' nor '-').", state)
                rtype = codes.REPLY_END
            return (state, text, rtype)
        else:
            raise GnatsNetworkException("Unparseable reply from server: '%s'" %
                                        raw_reply)

    def _read_server(self, parse):
        """ Read output from server until a line containing a single period
        is found.  Raise an exception if the connection closes early.

        This code has been profiled and optimized.
        """
        if parse:
            output = _DelimitedData()
        else:
            output = []
        while 1:
            try:
                line = unicode(self._sfile.readline(), gnats.ENCODING)
            except (IOError, socket.error):
                raise GnatsNetworkException('Error reading from gnatsd '
                    'at %s port %s' % (self.server.host, self.server.port))
            if gnats.protocol_debug:
                _LOG.debug("Read: %s", line[:-1])
            if not line:
                raise GnatsNetworkException("EOF encountered while reading " +
                                            "server output.")
            if line[0] == '.':
                if line.startswith('..'):
                    line = line[1:]
                elif line.startswith('.\r'):
                    # XXX??? This may be more restrictive than the actual
                    # proto spec.  I think that only a line beginning with a
                    # period is necessary...
                    break
            # XXX??? is it OK to strip all trailing whitespace?, or should I
            # just pull off \r, \n?  re.sub = 0.82s, rstrip = 0.32s, so 2xrstrip
            # is still faster than re.sub, if we have to go there.
            if not parse:
                # Don't strip newlines for parsed data
                line = line.rstrip()
            output.append(line)
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Read %d %s from server.",
                       len(output), parse and 'records' or 'lines')
        if parse:
            return output.records
        else:
            return output

    def _get_reply(self, parse=False):
        """ Process output from the server, calling _server_reply() to
        parse protocol lines, and _read_server() if additional data needs
        to be read. """
        rettext = []
        rtype = codes.REPLY_CONT
        while rtype == codes.REPLY_CONT:
            (state, text, rtype) = self._server_reply()
            if (state == codes.CODE_OK
                or state == codes.CODE_GREETING
                or state == codes.CODE_CLOSING):
                rettext.append(text)
                # nothing
            elif (state == codes.CODE_PR_READY
                  or state == codes.CODE_TEXT_READY):
                # XXX??? This will throw away any previously read lines.
                rettext = self._read_server(parse)
            elif (state == codes.CODE_SEND_PR
                  or state == codes.CODE_SEND_TEXT):
                pass
            elif (state == codes.CODE_INFORMATION_FILLER):
                # nothing
                pass
            elif (state == codes.CODE_INFORMATION):
                rettext.append(text)
            # TODO gnatsweb.pl ignores 416 specifically.  I don't see a reason
            # to do this, but I might find one later...
            #elif (state == codes.CODE_INVALID_LIST):
            #    pass
            elif (state == codes.CODE_NO_PRS_MATCHED):
                return
            elif (state >= '400' and state <= '799'):
                # 400 - 699 are errors of varying levels of severity
                if (state == codes.CODE_NO_ACCESS):
                    if hasattr(self, 'database'):
                        errmsg = 'You do not have access to database "%s"' % \
                            getattr(self, 'database').name
                    else:
                        errmsg = 'Access denied'
                    raise GnatsAccessException(errmsg, state)
                else:
                    rettext.append(text)
                    if rtype != codes.REPLY_CONT:
                        raise GnatsException("Error: %s - %s" %
                            (state, '\n'.join(rettext)), state)
                    else:
                        if state > "500":
                            # Errors in the 400s are problems with user input
                            # and the like, while the 600s are "real" problems
                            _LOG.warning("Received error code %s: '%s'",
                                         state, text)
            else:
                # gnatsd returned a state, but we don't know what it is
                if self.strict_protocol:
                    raise GnatsNetworkException\
                        ("unknown state '%s' from gnatsd, with message '%s'" %
                         (state, text), state)
                else:
                    rettext.append(text)
        return rettext

    # Utility methods

    _DOT_ESCAPE_RE = re.compile(r'^\.', re.MULTILINE)
    def _send_text(self, text):
        """ Send the text to gnatsd, after escaping leading periods.  Used
        by check, subm, edit. """
        # Escape leading dots
        escaped = self._DOT_ESCAPE_RE.sub('..', text).\
            encode(gnats.ENCODING, gnats.ENCODING_ERROR)
        if gnats.protocol_debug:
            _LOG.debug("Sending: %s", escaped)
        try:
            self._sfile.write(escaped)
            self._sfile.write('\n.\r\n')
            self._sfile.flush()
        except (IOError, socket.error):
            raise GnatsNetworkException('Error sending data to '
                'gnatsd at %s port %s' % (self.server.host, self.server.port))
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Sent %d bytes to gnatsd", len(escaped))

    _ACCESS_LEVEL_RE = re.compile(r"User access level set to '(\w*)'")
    def _parse_access_level(self, srv_output):
        mo = self._ACCESS_LEVEL_RE.match(srv_output)
        if mo:
            access_level = mo.group(1)
        else:
            access_level = 'none'
        return access_level

    # Database level commands

    def dbls(self):
        """ Return a list of databases on the server """
        output = self.command('DBLS')
        return output

    def dbdesc(self, dbname):
        """ DBDESC <database>
        return description of <database> """
        return self.command("DBDESC %s" % dbname)[0]

    def chdb(self, dbname, user='', passwd='', userpass=None):
        """ CHDB <database> [<user> [<passwd>]]
        change GNATS ROOT to <database>
        """
        if userpass is not None:
            user = userpass[0]
            passwd = userpass[1]
        if user is None: user = ''
        if passwd is None: passwd = ''
        output = self.command('CHDB %s %s %s' % (dbname, user, passwd))
        access_level = self._parse_access_level(output[1])

        # check access level.  if < view, make them log in again.
        # it might be better to allow "create-only" access for users
        # with 'submit' access.
        if codes.LEVEL_TO_CODE[access_level] < codes.LEVEL_TO_CODE['view']:
            raise GnatsAccessException(("User '%s' does not have view access " +
                                 "to database '%s'.") % (user, dbname))
        return access_level

    def user(self, name='', passwd=''):
        """ USER <name> [<passwd>]  Sets the current user
        USER                    Report current access level
        """
        output =  self.command("USER %s %s" % (name, passwd))
        if name:
            return self._parse_access_level(output[1])
        else:
            return output[0]

    def lkdb(self):
        """ LKDB
        lock the main GNATS database """
        return self.command("LKDB")

    def undb(self):
        """ UNDB
        unlock the main GNATS database """
        return self.command("UNDB")

    # Commands for querying and fetching PRs

    def qfmt(self, format):
        """ QFMT <query format>
        Use the specified query format to format the output of the query
        """
        return self.command("QFMT %s" % format)

    def tqfmt(self, field_name, format):
        """ TQFMT <table field> <query format>
        Use the specified query format to format the output of table field
        rows in the query
        """
        return self.command("TQFMT %s %s" % (field_name, format))

    def expr(self, expr):
        """ EXPR <expression>
        restrict search to PRs that match the query expression
        """
        return self.command("EXPR %s" % expr)

    def quer(self, prs='', parse=False):
        """ The search itself is performed by QUER.  It may be invoked
        with no arguments,  which will search the entire database given
        the constraints of EXPR, or with one or more PRs in its command,
        which will search those PRs specifically.
        """
        if prs is not None and not (isinstance(prs, basestring) or
                isinstance(prs, int)):
            prs = ' '.join([str(pr) for pr in prs])
        if prs is None: prs = ''
        return self.command("QUER %s" % prs, parse)

    def rset(self):
        """ RSET
        reset internal QFMT and EXPR settings to initial defaults. """
        return self.command("RSET")

    # Commands for manipulating PRs

    def editaddr(self, address):
        """ EDITADDR <address>
        set e-mail address to <address> """
        return self.command("EDITADDR %s" % address)

    def chek(self, pr, initial=False):
        """ CHEK [initial]
        check PR text for errors """
        self.command("CHEK %s" % (initial and "initial" or ""))
        self._send_text(pr)
        return self._get_reply()

    def lock(self, prnum, user, pid, session_id=''):
        """ LOCK <PR> <user> <pid> [session-id]
        lock <PR> for <user> with optional <pid>
        and optional [session-id] and return PR text
        """
        return self.command("LOCK %s %s %s %s" % (prnum, user, pid, session_id))

    def lockn(self, prnum, user, pid, session_id=''):
        """ LOCK <PR> <user> <pid> [session-id]
        lock <PR> for <user> with optional <pid>
        and optional [session-id] and DO NOT return PR text
        """
        try:
            return self.command("LOCKN %s %s %s %s" %
                                    (prnum, user, pid, session_id))
        except GnatsException, e:
            if e.code == '600':
                # LOCKN not implemented, fall back to LOCK
                return self.command("LOCK %s %s %s %s" %
                                    (prnum, user, pid, session_id))
            else:
                raise


    def unlk(self, prnum):
        """ UNLK <PR>
        unlock <PR> """
        return self.command("UNLK %s" % prnum)

    def subm(self, pr, session_id=''):
        """ SUBM [session-id]
        submit a new PR with an optional [session-id] for multi field
        edit session.
        """
        self.command("SUBM %s" % session_id)
        self._send_text(pr)
        return self._get_reply()

    def appn(self, prnum, fieldname, value, scope_id='', session_id='',
             _cmd='APPN'):
        """ APPN <PR> <field[{scope}]> [session-id]
        append to contents of <field[{scope}]> in <PR>
        and optional [session-id] for multi field edit session
        """
        if scope_id:
            fspec = "%s{%s}" % (fieldname, scope_id)
        else:
            fspec = fieldname
        self.command("%s %s %s %s" % (_cmd, prnum, fspec, session_id))
        self._send_text(value)
        return self._get_reply()

    def repl(self, prnum, fieldname, value, scope_id='', session_id=''):
        """ REPL <PR> <field[{scope}]> [session-id]
        replace contents of <field[{scope}]> in <PR>
        and optional [session-id] for multi field edit session
        """
        return self.appn(prnum, fieldname, value, scope_id, session_id, 'REPL')

    def tappn(self, prnum, fieldname, value_dict, session_id=''):
        """ TAPPN <pr_num> <fieldname> <separator> <col_name ... col_name>
        Append to contents of <fieldname> in <PR>
        and optional [session-id] for multi field edit session
        """
        cols = []
        vals = []
        for col, val in value_dict.iteritems():
            cols.append(col)
            vals.append(val)
        self.command("TAPPN %s %s %s %s %s" %
             (prnum, fieldname, codes.COL_SEP, ' '.join(cols), session_id))
        self._send_text(codes.COL_SEP.join(vals))
        return self._get_reply()

    def trepl(self, prnum, fieldname, row_num, value_dict, session_id=''):
        """ TREPL <pr_num> <fieldname> <row_num> <sep> <col_name ... col_name>
        Replace contents of <fieldname> row <row_num> in <PR>
        and optional [session-id] for multi field edit session
        """
        cols = []
        vals = []
        for col, val in value_dict.iteritems():
            cols.append(col)
            vals.append(val)
        self.command("TREPL %s %s %s row-id %s %s" % (prnum, fieldname,
            codes.COL_SEP, ' '.join(cols), session_id))
        text = row_num + codes.COL_SEP + codes.COL_SEP.join(vals)
        self._send_text(text)
        return self._get_reply()

    def edit(self, prnum, pr):
        """ EDIT <PR>               check in edited <PR>
        """
        self.command("EDIT %s" % prnum)
        self._send_text(pr)
        return self._get_reply()

    def delete(self, prnum):
        """ DELETE <PR>
        Delete the specified <PR>
        """
        return self.command("DELETE %s" % prnum)

    def vfld(self, field, text):
        """ VFLD <field>            validate that the provided text is valid
        for the specified field
        """
        self.command("VFLD %s" % field)
        self._send_text(text)
        return self._get_reply()

    # Commands for querying metadata

    def cfgt(self):
        """ Return the timestamp of the gnatsd configuration files. """
        return self.command("CFGT")[0]

    def list(self, list_type):
        """ LIST <list type>
        list info of the specified type
        """
        return self.command("LIST %s" % list_type)

    def ftyp(self, fields):
        """ FTYP <field> [<field> ...]
        return the datatype of <field>
        """
        if isinstance(fields, basestring):
            fields = [fields]
        return self.command("FTYP %s" % ' '.join(fields))

    def atyp(self, axes):
        """ ATYP <axis> [<axis> ...]
        return the datatype of <axis>
        """
        if isinstance(axes, basestring):
            axes = [axes]
        return self.command("ATYP %s" % ' '.join(axes))

    def fdsc(self, fields):
        """ FDSC <field> [<field> ...]
        return the description of <field> """
        if isinstance(fields, basestring):
            fields = [fields]
        return self.command("FDSC %s" % ' '.join(fields))

    def adsc(self, axes):
        """ ADSC <axis> [<axis> ...]
        return the description of <axis>
        """
        if isinstance(axes, basestring):
            axes = [axes]
        return self.command("ADSC %s" % ' '.join(axes))

    def fvld(self, field, *subfield_args):
        """ FVLD <field> [<subfield>] [<search-string> [<subfield:...>]]
        return a string or regexp describing the legal values for <field>

        Supplying "*" as the second arg will retrieve values for all subfields.
        """
        return self.command("FVLD %s %s" % (field, ' '.join(subfield_args)))

    def avld(self, axis):
        """ AVLD <axis>
        return a string or regexp describing the legal values for <axis>
        """
        return self.command("AVLD %s" % axis)

    def admv(self, field, key, subfield=''):
        """ ADMV <field> <key> [<subfield>]
        Retrieve a record from a field's admin db
        """
        return self.command("ADMV %s %s %s" % (field, key, subfield))

    def ftypinfo(self, field, prop):
        """ FTYPINFO <field> <separators | constraints | subfields | columns>
        return info about a property of the specified field
        """
        return self.command("FTYPINFO %s %s" % (field, prop))

    def fieldflags(self, fields):
        """ FIELDFLAGS <field> [<field> ...]
        List the field flags for the specified
        fields
        """
        if isinstance(fields, basestring):
            fields = [fields]
        return self.command("FIELDFLAGS %s" % ' '.join(fields))

    def inputdefault(self, fields):
        """ INPUTDEFAULT <field> [<field> ...]
        List the suggested default input values for the specified field(s)
        """
        if isinstance(fields, basestring):
            fields = [fields]
        return self.command("INPUTDEFAULT %s" % ' '.join(fields))

    # Misc commands

    def close(self):
        """ Issue a QUIT and close the socket. """
        retval = self.command("QUIT")
        self._sock.close()
        return retval

    def quit(self):
        """ Alias for close(). """
        return self.close()

    def auth(self, auth_type):
        """ Something about authentication types...

        This protocol command is not documented in HELP.
        """
        return self.command("AUTH %s" % auth_type)

    def help(self):
        """ Return the gnatsd built in protocol help text. """
        return self.command("HELP")


class _DelimitedData(object):
    """ Collect input and parse into records based on field & record delimiters.
    """

    _record_separator = codes.RECORD_SEP + '\r\n'
    _rs_len = len(_record_separator)

    def __init__(self):
        self.records = []
        self._buffer = []

    def __len__(self):
        return len(self.records)

    def append(self, value=''):
        """ Append a chunk of data, which may hold bits of multiple records. """
        start = 0
        while 1:
            index = value.find(self._record_separator, start)
            if index > -1:
                # This chunk contains the end of a record, the beginning of
                # which may be in the buffer
                self._buffer.append(value[start:index])
                # Reconstruct the raw record, and split it on separators
                raw = ''.join(self._buffer)
                self.records.append(raw.split(codes.FIELD_SEP))
                self._buffer = []
                if len(value) > (index + self._rs_len):
                    # There's more to process
                    start = index + self._rs_len
                else:
                    break
            else:
                # chunk is merely part of a record, save it in the buffer
                self._buffer.append(value[start:])
                break
