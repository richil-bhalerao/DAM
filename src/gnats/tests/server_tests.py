#!/usr/bin/python
"""
Unit tests for gnats Server and ServerConnection

Dirk Bergstrom, dirk@juniper.net, 2008-04-24

Copyright (c) 2008, Juniper Networks, Inc.
All rights reserved.
"""
import unittest
from pmock import *
import socket

import gnats
from gnats import GnatsAccessException, GnatsNetworkException, codes
from gnats import Server
from gnats import server

# Shut up logging during the tests
import logging
logging.disable(logging.FATAL)

class FakeSocketFile(object):
    """ Mock version of a socket file object that pretends to be connected
    to a gnatsd.  The contents of reply_buf are doled out line by line on
    successive calls to readline(). """

    def __init__(self):
        self.inputs = []
        self.reply_buf = []
        self.flushed = False

    def set_reply_buf(self, stuff):
        if isinstance(stuff, basestring):
            revd = stuff.splitlines(True)
        else:
            revd = list(stuff)
        revd.reverse()
        self.reply_buf = revd

    def readline(self):
        return self.reply_buf.pop()

    def write(self, val):
        self.inputs.append(val)

    def flush(self):
        self.flushed = True


def setup_fake_socket_server_and_connection():
    """ Setup the fake socket library and objects for gnats. """
    fake_sfile = FakeSocketFile()
    # A mock version of the socket library factory and socket objects
    # that will spit out our FakeSocketFile.
    socksockmock = Mock()
    socksockmock.expects(at_least_once()).method('connect')
    sockmock = Mock()
    socksockmock.expects(at_least_once()).makefile().\
                          will(return_value(fake_sfile))
    sockmock.expects(at_least_once()).method('socket').\
                          will(return_value(socksockmock))
    server.socket = sockmock
    # Needed for error testing
    server.socket.error = socket.error
    srv = Server('somehost')
    fake_sfile.set_reply_buf("200 somehost GNATS server 4.0-DEV ready.")
    conn = srv.get_connection()
    return fake_sfile, srv, conn

class T01_ServerTest(unittest.TestCase):
    """ Test gnats.Server """

    def setUp(self):
        self.fake_sfile, self.srv, __ = \
            setup_fake_socket_server_and_connection()

    def test_01_server_host_port(self):
        """ Create Server and check host/port """
        self.assertEqual(self.srv.host, 'somehost')
        self.assertEqual(self.srv.port, codes.DEFAULT_PORT)

    def test_02_server_get_conection(self):
        """ get_connection() returns Connection and sets gnatsd_version """
        self.fake_sfile.set_reply_buf(
            "200 spyro.juniper.net GNATS server 4.0-DEV ready.\r\n")
        conn = self.srv.get_connection()
        self.assertEqual(self.fake_sfile, conn._sfile)
        self.assertEqual(self.srv.gnatsd_version, '4.0-DEV')

    def test_03_server_list_databases(self):
        """ list_databases() returns correct list """
        self.fake_sfile.set_reply_buf(
"""200 spyro.juniper.net GNATS server 4.0-DEV ready.\r
301 List follows.\r
default\r
request\r
.\r
""")
        self.assertEqual(self.srv.list_databases(), ['default', 'request'])

"""
    _CTRL_STRIP_RE = re.compile(r'[\x01-\x08\x0a-\x1a]')
    def command(self, cmd, parse=False):
        "" Send the given protocol command and arguments to gnatsd,
        return the output as a list of lines.

        Most control characters are stripped out of the command before it
        is sent.  See package docs on 'allow_cmd_control_chars'.
        ""
        if gnats.allow_cmd_control_chars:
            fixed_cmd = cmd.replace('\n', ' ')
        else:
            fixed_cmd = self._CTRL_STRIP_RE.sub(' ', cmd)
        fixed_cmd = fixed_cmd.encode(gnats.ENCODING, gnats.ENCODING_ERROR)
        _LOG.debug("Sending command '%s'", fixed_cmd)
        self._sfile.write(fixed_cmd)
        self._sfile.write("\n")
        self._sfile.flush()
        return self._get_reply(parse)
"""
class T02_Protocol_command(unittest.TestCase):
    """ Test Connection.command(). """

    def setUp(self):
        self.fake_sfile, self.srv, self.conn = \
            setup_fake_socket_server_and_connection()
        self.conn._get_reply = self.fake_get_reply
        self.parse = -1

    def fake_get_reply(self, parse):
        self.parse = parse

    def test_01_sends_input(self):
        """ Sends input correctly """
        self.conn.command("foo bar")
        self.assertEquals(self.fake_sfile.inputs, ['foo bar', '\n'])
        self.assertEquals(self.fake_sfile.inputs, ['foo bar', '\n'])

    def test_02_flushes(self):
        """ Flushes socket """
        self.conn.command("foo bar")
        self.assertTrue(self.fake_sfile.flushed)

    def test_03_honors_parse(self):
        """ parse param is passed to _get_reply """
        self.conn.command("foo bar")
        self.assertFalse(self.parse)
        self.conn.command("foo bar", True)
        self.assertTrue(self.parse)

    def test_04_strips_nl(self):
        """ Strips newlines from input """
        self.conn.command("foo\nbar\n")
        self.assertEquals(self.fake_sfile.inputs, ['foo bar ', '\n'])

    def test_05_strips_ctrl(self):
        """ Strips control characters from input """
        self.conn.command("foo\x0bbar\x06")
        self.assertEquals(self.fake_sfile.inputs, ['foo bar ', '\n'])

    def test_06_allow_cmd_ctrl(self):
        """ gnats.allow_cmd_control_chars stops ctrl stripping """
        try:
            gnats.allow_cmd_control_chars = True
            self.conn.command("foo\x0bbar\x06")
        finally:
            gnats.allow_cmd_control_chars = False
        self.assertEquals(self.fake_sfile.inputs, ['foo\x0bbar\x06', '\n'])

    def test_07_allow_cmd_ctrl_nl(self):
        """ gnats.allow_cmd_control_chars still strips newlines """
        try:
            gnats.allow_cmd_control_chars = True
            self.conn.command("foo\nbar\x06")
        finally:
            gnats.allow_cmd_control_chars = False
        self.assertEquals(self.fake_sfile.inputs, ['foo bar\x06', '\n'])

    def test_04_send_text_ioerror(self):
        """ command handles IOError """
        def raising_sfile_write(input):
            raise IOError("boo!")
        self.fake_sfile.write = raising_sfile_write
        self.assertRaises(GnatsNetworkException, self.conn.command, "howdy")

    def test_05_send_text_socketerror(self):
        """ command handles socket.error """
        def raising_sfile_write(input):
            raise socket.error()
        self.fake_sfile.write = raising_sfile_write
        self.assertRaises(GnatsNetworkException, self.conn.command, "howdy")



class T02a_Protocol_server_reply(unittest.TestCase):
    """ Test Connection._server_reply() (low-level protocol parsing). """

    def setUp(self):
        self.fake_sfile, self.srv, self.conn = \
            setup_fake_socket_server_and_connection()

    def test_01_server_reply_unparseable_reply(self):
        """ _server_reply raises on unparseable reply """
        self.fake_sfile.reply_buf = ['not even remotely parseable\r\n']
        self.failUnlessRaises(gnats.GnatsNetworkException,
                              self.conn._server_reply)

    def test_02_server_reply_bad_reply_type(self):
        """ _server_reply raises on bad reply type """
        self.fake_sfile.reply_buf = ['666+Evil Reply Type\r\n']
        self.failUnlessRaises(gnats.GnatsNetworkException,
                              self.conn._server_reply)

    def test_03_server_reply_reply_cont(self):
        """ _server_reply returns REPLY_CONT """
        self.fake_sfile.reply_buf = ['999-Reply Cont Type\r\n']
        self.assertEqual(self.conn._server_reply()[2], gnats.codes.REPLY_CONT)

    def test_04_server_reply_reply_end(self):
        """ _server_reply returns REPLY_END """
        self.fake_sfile.reply_buf = ['888 Reply End Type\r\n']
        self.assertEqual(self.conn._server_reply()[2], gnats.codes.REPLY_END)

    def test_05_server_reply_state(self):
        """ _server_reply returns correct reply state """
        self.fake_sfile.reply_buf = [gnats.codes.CODE_OK +' Reply state foo\r\n']
        self.assertEqual(self.conn._server_reply()[0], gnats.codes.CODE_OK)

    def test_06_server_reply_text(self):
        """ _server_reply returns correct reply text """
        self.fake_sfile.reply_buf = ['350 Wacked out text\r\n']
        self.assertEqual(self.conn._server_reply()[1], 'Wacked out text')

    def test_07_err_code_in_exc(self):
        """ _get_reply includes error code in exception """
        try:
            self.fake_sfile.set_reply_buf('600+I hate you\r\n')
            self.conn._server_reply()
            self.fail("_server_reply didn't raise as expected.")
        except gnats.GnatsNetworkException, e:
            self.assertEqual(e.code, '600')

    def raising_sfile_readline(self):
        raise IOError("boo!")

    def test_08_server_reply_ioerror(self):
        """ _server_reply handles IOError """
        self.fake_sfile.set_reply_buf('line 1\n..l2\nl3\nl4\n.\r\n')
        self.fake_sfile.readline = self.raising_sfile_readline
        self.assertRaises(GnatsNetworkException, self.conn._read_server, False)


class T03_Protocol_read_server(unittest.TestCase):
    """ Test Connection._read_server() (low-level protocol parsing). """

    def setUp(self):
        self.fake_sfile, self.srv, self.conn = \
            setup_fake_socket_server_and_connection()

    def test_01_read_server_early_eof(self):
        """ _read_server raises on unexpected EOF """
        self.fake_sfile.set_reply_buf(['line 1\r\n', '', "Shouldn't read\r\n"])
        self.failUnlessRaises(gnats.GnatsNetworkException,
                              self.conn._read_server, False)

    def test_02_read_server_stop_period(self):
        """ _read_server stops at period """
        self.fake_sfile.set_reply_buf('line 1\nl2\nl3\n.\r\nl4\r\n')
        self.assertEquals(self.conn._read_server(False)[-1], 'l3')

    def test_03_read_server_unescape_period(self):
        """ _read_server unescapes periods """
        self.fake_sfile.set_reply_buf('line 1\n..l2\nl3\nl4\n.\r\n')
        out = self.conn._read_server(False)
        self.assertEquals(len(out), 4)
        self.assertEquals(out[1], '.l2')

    def test_04_read_server_parsed(self):
        """ _read_server parses formatted data """
        self.fake_sfile.set_reply_buf('x\037y\036\r\na\037b\037c\036\r\n.\r\n')
        out = self.conn._read_server(True)
        self.assertEquals(len(out), 2)
        self.assertEquals(len(out[0]), 2)
        self.assertEquals(len(out[1]), 3)
        self.assertEquals(out[1][1], 'b')

    def test_05_read_server_parsed_newlines(self):
        """ _read_server parses formatted data with embedded newlines """
        self.fake_sfile.\
            set_reply_buf('x\037y\nz\n0\n1\036\r\na\nq\nw\037b\037c\036\r\n.\r\n')
        out = self.conn._read_server(True)
        self.assertEquals(len(out), 2)
        self.assertEquals(len(out[0]), 2)
        self.assertEquals(len(out[1]), 3)
        self.assertEquals(out[1][0], 'a\nq\nw')

    def raising_sfile_readline(self):
        raise IOError("boo!")

    def test_06_read_server_ioerror(self):
        """ _read_server handle IOError """
        self.fake_sfile.set_reply_buf('line 1\n..l2\nl3\nl4\n.\r\n')
        self.fake_sfile.readline = self.raising_sfile_readline
        self.assertRaises(GnatsNetworkException, self.conn._read_server, False)


class T04_Protocol_get_reply(unittest.TestCase):
    """ Test Connection._get_reply() (low-level protocol parsing). """

    def setUp(self):
        self.fake_sfile, self.srv, self.conn = \
            setup_fake_socket_server_and_connection()

    def test_01_get_reply_unknown_state(self):
        """ _get_reply raises on unknown state """
        self.fake_sfile.set_reply_buf('999 This is funky\r\n')
        self.failUnlessRaises(gnats.GnatsNetworkException,
                              self.conn._get_reply, False)

    def test_02_get_reply_unknown_state_no_strict(self):
        """ _get_reply doesn't raise on unknown state with strict_protocol = False """
        self.fake_sfile.set_reply_buf('999 This is funky\r\n')
        self.conn.strict_protocol = False
        self.assertEquals(self.conn._get_reply(False), ['This is funky'])

    def test_03_get_reply_error_state(self):
        """ _get_reply raises on an error state """
        self.fake_sfile.set_reply_buf('600 I hate you\r\n')
        self.failUnlessRaises(gnats.GnatsException, self.conn._get_reply, False)

    def test_04_get_reply_no_access(self):
        """ _get_reply raises GnatsAccessException on NO_ACCESS """
        self.fake_sfile.set_reply_buf('422 Access denied, buddy\r\n')
        self.failUnlessRaises(gnats.GnatsAccessException,
                              self.conn._get_reply, False)

    def test_05_get_reply_no_prs_matched(self):
        """ _get_reply NO_PRS_MATCHED """
        self.fake_sfile.set_reply_buf('220 No PRs Matched\r\n')
        self.assertEquals(self.conn._get_reply(False), None)

    def test_06_get_reply_send_pr(self):
        """ _get_reply SEND_PR"""
        self.fake_sfile.set_reply_buf('211 Send PR\r\n')
        self.assertEquals(self.conn._get_reply(False), [])

    def test_07_get_reply_send_text(self):
        """ _get_reply SEND TEXT"""
        self.fake_sfile.set_reply_buf('212 Send Text\r\n')
        self.assertEquals(self.conn._get_reply(False), [])

    def test_08_get_reply_greeting(self):
        """ _get_reply GREETING """
        self.fake_sfile.set_reply_buf('200 Greeting\r\n')
        self.assertEquals(self.conn._get_reply(False), ['Greeting'])

    def test_09_get_reply_ok(self):
        """ _get_reply OK """
        self.fake_sfile.set_reply_buf('210 OK\r\n')
        self.assertEquals(self.conn._get_reply(False), ['OK'])

    def test_10_get_reply_closing(self):
        """ _get_reply CLOSING """
        self.fake_sfile.set_reply_buf('201 Closing\r\n')
        self.assertEquals(self.conn._get_reply(False), ['Closing'])

    def test_11_get_reply_information_filler(self):
        """ _get_reply INFORMATION_FILLER """
        self.fake_sfile.set_reply_buf('351 Filler\r\n')
        self.assertEquals(self.conn._get_reply(False), [])

    def test_12_get_reply_information_single(self):
        """ _get_reply CODE_INFORMATION single line """
        self.fake_sfile.set_reply_buf('350 Foo Info\r\n')
        self.assertEquals(self.conn._get_reply(False), ['Foo Info'])

    def test_13_get_reply_information_multi(self):
        """ _get_reply CODE_INFORMATION multi-line """
        self.fake_sfile.set_reply_buf('350-Foo Info\r\n350 Bar Info\r\n')
        self.assertEquals(self.conn._get_reply(False), ['Foo Info', 'Bar Info'])

    def test_14_get_reply_pr_ready(self):
        """ _get_reply PR_READY returns text """
        self.fake_sfile.set_reply_buf('300 PR Ready\r\nprl1\nprl2\nprl3\n.\r\n')
        self.assertEquals(self.conn._get_reply(False), ['prl1', 'prl2', 'prl3'])

    def test_15_get_reply_text_ready(self):
        """ _get_reply TEXT_READY returns text """
        self.fake_sfile.set_reply_buf('301 Text Ready\r\ntextl1\ntextl2\ntextl3\n.\r\n')
        self.assertEquals(self.conn._get_reply(False),
                          ['textl1', 'textl2', 'textl3'])

    def test_16_get_reply_pr_ready_parsed(self):
        """ _get_reply PR_READY with parse=True returns parsed text """
        self.fake_sfile.set_reply_buf('300 PR\npr\037l1\036\r\npr\037l2\036\r\n.\r')
        self.assertEquals(self.conn._get_reply(True),
                          [['pr', 'l1'], ['pr', 'l2']])

    def test_17_get_reply_honors_reply_cont(self):
        """ _get_reply stops when type != REPLY_CONT """
        self.fake_sfile.set_reply_buf('350-Foo\r\n350 Bar\r\n350 Baz\r\n')
        self.assertEquals(self.conn._get_reply(False), ['Foo', 'Bar'])

    def test_18_err_code_in_exc(self):
        """ _get_reply includes error code in exception """
        try:
            self.fake_sfile.set_reply_buf('600 I hate you\r\n')
            self.conn._get_reply(False)
            self.fail("_get_reply didn't raise as expected.")
        except gnats.GnatsException, e:
            self.assertEqual(e.code, '600')

    def test_19_multiple_errs_in_exc(self):
        """ _get_reply includes multiple error messages exception (PR 394419) """
        try:
            self.fake_sfile.set_reply_buf(['403-Bad field XXX\r\n',
                                          '403 Bad field YYY\r\n'])
            self.conn._get_reply(False)
            self.fail("_get_reply didn't raise as expected.")
        except gnats.GnatsException, e:
            self.assertTrue(e.message.find('XXX') > -1 and
                            e.message.find('YYY') > -1)


class T05_UtilityMethods(unittest.TestCase):
    """ Test utility methods. """

    def setUp(self):
        self.fake_sfile, self.srv, self.conn = \
            setup_fake_socket_server_and_connection()

    def test_01_send_text_string(self):
        """ _send_text string does proper escaping"""
        text = ['This is some text', '.line starting with period']
        self.assertEquals(self.conn._send_text('\n'.join(text)), None)
        self.assertEquals(self.fake_sfile.inputs,
                          [text[0] + '\n.' + text[1], '\n.\r\n'])

    def test_02_parse_access_level(self):
        """ _parse_access_level parses correctly """
        self.assertEquals(
            self.conn._parse_access_level("User access level set to 'edit'"),
            'edit')

    def test_03_parse_access_level_bad_input(self):
        """ _parse_access_level returns 'none' on bad input """
        self.assertEquals(self.conn._parse_access_level("duh"), 'none')

    def raising_sfile_write(self, input):
        raise IOError("boo!")

    def test_04_send_text_ioerror(self):
        """ _send_text handles IOError """
        self.fake_sfile.write = self.raising_sfile_write
        self.assertRaises(GnatsNetworkException, self.conn._send_text, "howdy")


class T06_ProtocolCmdMethods(unittest.TestCase):
    """ Test Connection protocol commands. """

    def setUp(self):
        self.fake_sfile, self.srv, self.conn = \
            setup_fake_socket_server_and_connection()
        self.conn.command = self._fake_command
        self.cmd_in = ''
        self.conn._send_text = self._fake_send_text
        self.send_text_in = ''
        self.conn._get_reply = lambda: 'boo'
        self.parse = None
        self.cmd_out = []

    def _fake_command(self, cmd, parse=False):
        self.cmd_in = cmd
        self.parse = parse
        return self.cmd_out

    def _fake_send_text(self, txt):
        self.send_text_in = txt

    def test_01_dbls(self):
        """ DBLS """
        self.cmd_out = ['default', 'foo']
        out = self.conn.dbls()
        self.assertEquals(self.cmd_in, 'DBLS')
        self.assertEquals(out, ['default', 'foo'])

    def test_02_dbdesc(self):
        """ DBDESC """
        self.cmd_out = ['Foo database']
        out = self.conn.dbdesc('foo')
        self.assertEquals(self.cmd_in, 'DBDESC foo')
        self.assertEquals(out, 'Foo database')

    def test_03_chdb_no_user_pass(self):
        """ CHDB no user/pass """
        self.cmd_out = ["Now accessing GNATS database 'default'",
                        "User access level set to 'edit'"]
        out = self.conn.chdb('default')
        self.assertEquals(self.cmd_in, 'CHDB default  ')
        self.assertEquals(out, 'edit')

    def test_04_chdb_user_pass(self):
        """ CHDB with user/pass """
        self.cmd_out = ["Now accessing GNATS database 'default'",
                        "User access level set to 'admin'"]
        out = self.conn.chdb('default', 'gnats', 'gnats')
        self.assertEquals(self.cmd_in, 'CHDB default gnats gnats')
        self.assertEquals(out, 'admin')

    def test_05_chdb_raises_on_no_access(self):
        """ CHDB raises on no access """
        self.cmd_out = ["Now accessing GNATS database 'default'",
                        "User access level set to 'none'"]
        self.failUnlessRaises(GnatsAccessException, self.conn.chdb, 'default')
        self.assertEquals(self.cmd_in, 'CHDB default  ')

    def test_06_user_username_passwd(self):
        """ USER username passwd"""
        self.cmd_out = ["Now accessing GNATS database 'default'",
                        "User access level set to 'view'"]
        out = self.conn.user('fred', 'foo')
        self.assertEquals(self.cmd_in, 'USER fred foo')
        self.assertEquals(out, 'view')

    def test_07_user_no_userpass(self):
        """ USER with no username reports access level """
        self.cmd_out = ['edit']
        out = self.conn.user()
        self.assertEquals(self.cmd_in, 'USER  ')
        self.assertEquals(out, 'edit')

    def test_08_lkdb(self):
        """ LKDB """
        self.cmd_out = 'GNATS database is now locked.'
        out = self.conn.lkdb()
        self.assertEquals(self.cmd_in, 'LKDB')
        self.assertEquals(out, 'GNATS database is now locked.')

    def test_09_undb(self):
        """ UNDB """
        self.cmd_out = 'GNATS database is now unlocked.'
        out = self.conn.undb()
        self.assertEquals(self.cmd_in, 'UNDB')
        self.assertEquals(out, 'GNATS database is now unlocked.')

    def test_10_qfmt(self):
        """ QFMT """
        self.cmd_out = ['Ok.']
        out = self.conn.qfmt('"%s|%s" some format')
        self.assertEquals(self.cmd_in, 'QFMT "%s|%s" some format')
        self.assertEquals(out, ['Ok.'])

    def test_10a_tqfmt(self):
        """ TQFMT """
        self.cmd_out = ['Ok.']
        out = self.conn.tqfmt('some-field', '"%s|%s" some format')
        self.assertEquals(self.cmd_in, 'TQFMT some-field "%s|%s" some format')
        self.assertEquals(out, ['Ok.'])

    def test_11_expr(self):
        """ EXPR """
        self.cmd_out = ['Ok.']
        out = self.conn.expr('state="closed"')
        self.assertEquals(self.cmd_in, 'EXPR state="closed"')
        self.assertEquals(out, ['Ok.'])

    def test_12_quer_no_prs(self):
        """ QUER with no pr number list """
        self.cmd_out = ['abcd']
        out = self.conn.quer()
        self.assertEquals(self.cmd_in, 'QUER ')
        self.assertEquals(self.parse, False)
        self.assertEquals(out, ['abcd'])

    def test_13_quer_prs_string(self):
        """ QUER with pr number list """
        self.cmd_out = ['abcd']
        out = self.conn.quer(prs='123')
        self.assertEquals(self.cmd_in, 'QUER 123')
        self.assertEquals(self.parse, False)
        self.assertEquals(out, ['abcd'])

    def test_14_quer_prs_list(self):
        """ QUER with pr number list """
        self.cmd_out = ['abcd']
        out = self.conn.quer(prs=('123', '456'))
        self.assertEquals(self.cmd_in, 'QUER 123 456')
        self.assertEquals(self.parse, False)
        self.assertEquals(out, ['abcd'])

    def test_15_quer_parse(self):
        """ QUER with parse == True """
        self.cmd_out = ['abcd']
        out = self.conn.quer(parse=True)
        self.assertEquals(self.cmd_in, 'QUER ')
        self.assertEquals(self.parse, True)
        self.assertEquals(out, ['abcd'])

    def test_16_rset(self):
        """ RSET """
        self.cmd_out = ['foo']
        out = self.conn.rset()
        self.assertEquals(self.cmd_in, 'RSET')
        self.assertEquals(out, ['foo'])

    # Commands for manipulating PRs

    def test_17_editaddr(self):
        """ EDITADDR """
        self.cmd_out = ['Ok.']
        out = self.conn.editaddr('joe@blo.com')
        self.assertEquals(self.cmd_in, 'EDITADDR joe@blo.com')
        self.assertEquals(out, ['Ok.'])

    def test_18_chek(self):
        """ CHEK """
        self.cmd_out = ['']
        text = 'this is a test'
        out = self.conn.chek(text)
        self.assertEquals(self.cmd_in, 'CHEK ')
        self.assertEquals(out, 'boo')
        self.assertEquals(self.send_text_in, text)

    def test_18_chek_initial(self):
        """ CHEK initial """
        self.cmd_out = ['']
        text = 'this is a test'
        out = self.conn.chek(text, initial=True)
        self.assertEquals(self.cmd_in, 'CHEK initial')
        self.assertEquals(out, 'boo')
        self.assertEquals(self.send_text_in, text)

    def test_19_lock(self):
        """ LOCK """
        self.cmd_out = ['this\nis\na\npr']
        out = self.conn.lock(1234, 'joeblo', '4321')
        self.assertEquals(self.cmd_in, 'LOCK 1234 joeblo 4321 ')
        self.assertEquals(out, ['this\nis\na\npr'])

    def test_19a_lockn(self):
        """ LOCKN """
        self.cmd_out = ['Ok.']
        out = self.conn.lockn(1234, 'joeblo', '4321')
        self.assertEquals(self.cmd_in, 'LOCKN 1234 joeblo 4321 ')
        self.assertEquals(out, ['Ok.'])

    def test_20_lock_w_session(self):
        """ LOCK with session """
        self.cmd_out = ['this\nis\na\npr']
        out = self.conn.lock(1234, 'joeblo', '4321', 'session')
        self.assertEquals(self.cmd_in, 'LOCK 1234 joeblo 4321 session')
        self.assertEquals(out, ['this\nis\na\npr'])

    def test_20a_lockn_w_session(self):
        """ LOCKN with session """
        self.cmd_out = ['Ok.']
        out = self.conn.lockn(1234, 'joeblo', '4321', 'session')
        self.assertEquals(self.cmd_in, 'LOCKN 1234 joeblo 4321 session')
        self.assertEquals(out, ['Ok.'])

    def test_21_unlk(self):
        """ UNLK """
        self.cmd_out = ['PR 1234 unlocked.']
        out = self.conn.unlk(1234)
        self.assertEquals(self.cmd_in, 'UNLK 1234')
        self.assertEquals(out, ['PR 1234 unlocked.'])

    def test_22_subm(self):
        """ SUBM """
        self.cmd_out = ['']
        text = 'this is a test'
        out = self.conn.subm(text)
        self.assertEquals(self.cmd_in, 'SUBM ')
        self.assertEquals(out, 'boo')
        self.assertEquals(self.send_text_in, text)

    def test_23_subm_session(self):
        """ SUBM with session"""
        self.cmd_out = ['']
        text = 'this is a test'
        out = self.conn.subm(text, session_id='foo')
        self.assertEquals(self.cmd_in, 'SUBM foo')
        self.assertEquals(out, 'boo')
        self.assertEquals(self.send_text_in, text)

    def test_24_appn(self):
        """ APPN """
        self.cmd_out = ['']
        text = 'this is a test'
        out = self.conn.appn(1234, 'field', text)
        self.assertEquals(self.cmd_in, 'APPN 1234 field ')
        self.assertEquals(out, 'boo')
        self.assertEquals(self.send_text_in, text)

    def test_25_appn_scope(self):
        """ APPN with scope """
        self.cmd_out = ['']
        text = 'this is a test'
        out = self.conn.appn(1234, 'field', text, scope_id=1)
        self.assertEquals(self.cmd_in, 'APPN 1234 field{1} ')
        self.assertEquals(out, 'boo')
        self.assertEquals(self.send_text_in, text)

    def test_26_appn_session(self):
        """ APPN with session """
        self.cmd_out = ['']
        text = 'this is a test'
        out = self.conn.appn(1234, 'field', text, session_id=1)
        self.assertEquals(self.cmd_in, 'APPN 1234 field 1')
        self.assertEquals(out, 'boo')
        self.assertEquals(self.send_text_in, text)

    def test_27_repl(self):
        """ REPL (shared code with appn()) """
        self.cmd_out = ['']
        text = 'this is a test'
        out = self.conn.repl(1234, 'field', text)
        self.assertEquals(self.cmd_in, 'REPL 1234 field ')
        self.assertEquals(out, 'boo')
        self.assertEquals(self.send_text_in, text)

    def test_28_edit(self):
        """ EDIT """
        self.cmd_out = ['']
        text = 'this is a test'
        out = self.conn.edit(1234, text)
        self.assertEquals(self.cmd_in, 'EDIT 1234')
        self.assertEquals(out, 'boo')
        self.assertEquals(self.send_text_in, text)

    def test_29_delete(self):
        """ DELETE """
        self.cmd_out = ['Boo']
        out = self.conn.delete(1234)
        self.assertEquals(self.cmd_in, 'DELETE 1234')
        self.assertEquals(out, ['Boo'])

    def test_30_vfld(self):
        """ VFLD """
        self.cmd_out = ['']
        text = 'this is a test'
        out = self.conn.vfld('field', text)
        self.assertEquals(self.cmd_in, 'VFLD field')
        self.assertEquals(out, 'boo')
        self.assertEquals(self.send_text_in, text)

    # commands for querying metadata

    def test_31_cfgt(self):
        """ CFGT """
        self.cmd_out = ['12345']
        out = self.conn.cfgt()
        self.assertEquals(self.cmd_in, 'CFGT')
        self.assertEquals(out, '12345')

    def test_32_list(self):
        """ LIST """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.list('foo'), ['test'])
        self.assertEquals(self.cmd_in, 'LIST foo')

    def test_33_ftyp_single(self):
        """ FTYP single field """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.ftyp('fld'), ['test'])
        self.assertEquals(self.cmd_in, 'FTYP fld')

    def test_34_ftyp_multi(self):
        """ FTYP multiple fields """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.ftyp(['fld', 'fld2', 'fld3']), ['test'])
        self.assertEquals(self.cmd_in, 'FTYP fld fld2 fld3')

    def test_35_atyp_single(self):
        """ ATYP single field """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.atyp('fld'), ['test'])
        self.assertEquals(self.cmd_in, 'ATYP fld')

    def test_36_atyp_multi(self):
        """ ATYP multiple fields """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.atyp(['fld', 'fld2', 'fld3']), ['test'])
        self.assertEquals(self.cmd_in, 'ATYP fld fld2 fld3')

    def test_37_fdsc_single(self):
        """ FDSC single field """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.fdsc('fld'), ['test'])
        self.assertEquals(self.cmd_in, 'FDSC fld')

    def test_38_fdsc_multi(self):
        """ FDSC multiple fields """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.fdsc(['fld', 'fld2', 'fld3']), ['test'])
        self.assertEquals(self.cmd_in, 'FDSC fld fld2 fld3')

    def test_39_adsc_single(self):
        """ ADSC single field """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.adsc('fld'), ['test'])
        self.assertEquals(self.cmd_in, 'ADSC fld')

    def test_40_adsc_multi(self):
        """ ADSC multiple fields """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.adsc(['fld', 'fld2', 'fld3']), ['test'])
        self.assertEquals(self.cmd_in, 'ADSC fld fld2 fld3')

    def test_41_fvld_simple(self):
        """ FVLD with a single field """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.fvld('field'), ['test'])
        self.assertEquals(self.cmd_in, 'FVLD field ')

    def test_42_fvld_complex(self):
        """ FVLD with subfields and such """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.fvld('field', 'subfields', 'more'), ['test'])
        self.assertEquals(self.cmd_in, 'FVLD field subfields more')

    def test_45_avld(self):
        """ AVLD """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.avld('axis'), ['test'])
        self.assertEquals(self.cmd_in, 'AVLD axis')

    def test_46_admv_no_subfield(self):
        """ ADMV with no subfield"""
        self.cmd_out = ['test']
        self.assertEquals(self.conn.admv('fld', 'key'), ['test'])
        self.assertEquals(self.cmd_in, 'ADMV fld key ')

    def test_46_admv_subfield(self):
        """ ADMV with subfield"""
        self.cmd_out = ['test']
        self.assertEquals(self.conn.admv('fld', 'key', subfield='sub'), ['test'])
        self.assertEquals(self.cmd_in, 'ADMV fld key sub')

    def test_47_ftypinfo(self):
        """ FTYPINFO """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.ftypinfo('field', 'prop'), ['test'])
        self.assertEquals(self.cmd_in, 'FTYPINFO field prop')

    def test_48_fieldflags_single(self):
        """ FIELDFLAGS single field """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.fieldflags('fld'), ['test'])
        self.assertEquals(self.cmd_in, 'FIELDFLAGS fld')

    def test_49_fieldflags_multi(self):
        """ FIELDFLAGS multiple fields """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.fieldflags(['fld', 'fld2', 'fld3']), ['test'])
        self.assertEquals(self.cmd_in, 'FIELDFLAGS fld fld2 fld3')

    def test_50_inputdefault_single(self):
        """ INPUTDEFAULT single field """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.inputdefault('fld'), ['test'])
        self.assertEquals(self.cmd_in, 'INPUTDEFAULT fld')

    def test_51_inputdefault_multi(self):
        """ INPUTDEFAULT multiple fields """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.inputdefault(['fld', 'fld2', 'fld3']), ['test'])
        self.assertEquals(self.cmd_in, 'INPUTDEFAULT fld fld2 fld3')

    # Misc commands

    def test_52_close(self):
        """ close / QUIT """
        smock = Mock().expects(once()).close()
        self.conn._sock = smock
        self.cmd_out = ['test']
        self.assertEquals(self.conn.close(), ['test'])
        self.assertEquals(self.cmd_in, 'QUIT')
        smock.verify()

    def test_53_auth(self):
        """ AUTH """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.auth('type'), ['test'])
        self.assertEquals(self.cmd_in, 'AUTH type')

    def test_54_help(self):
        """ HELP """
        self.cmd_out = ['test']
        self.assertEquals(self.conn.help(), ['test'])
        self.assertEquals(self.cmd_in, 'HELP')


classes = (
          T01_ServerTest,
          T02_Protocol_command,
          T02a_Protocol_server_reply,
          T03_Protocol_read_server,
          T04_Protocol_get_reply,
          T05_UtilityMethods,
          T06_ProtocolCmdMethods,
         )

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    suites = []
    for cl in classes:
        suites.append(unittest.makeSuite(cl, 'test'))
    runner.run(unittest.TestSuite(suites))
