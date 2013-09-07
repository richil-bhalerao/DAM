#!/usr/bin/python
"""
Unit tests for gnats DatabaseHandle class

Dirk Bergstrom, dirk@juniper.net, 2008-04-30

Copyright (c) 2008, Juniper Networks, Inc.
All rights reserved.
"""
import unittest

# Shut up logging during the tests
import logging
logging.disable(logging.FATAL)

import gnats
from gnats import Database, DatabaseHandle, codes
from gnats.tests.database_tests import FakeServerConnectionForDB

class TestExc(Exception):
    pass


class T01_MetadataAndUtilityMethods(unittest.TestCase):
    """ Various internal and external utility methods. """

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        self.db = Database(self.server, 'testdb', self.conn)
        self.dbh = self.db.get_handle('user', 'pass', self.conn)

    def test_01_conn(self):
        """ Connection """
        self.assertEqual(self.dbh.conn, self.conn)

    def test_02_database(self):
        """ database """
        self.assertEqual(self.dbh.database, self.db)

    def test_03_username(self):
        """ username """
        self.assertEqual(self.dbh.username, 'user')

    def test_04_password(self):
        """ passwd """
        self.assertEqual(self.dbh.passwd, 'pass')

    def test_05_access_level(self):
        """ access_level """
        self.assertEqual(self.dbh.access_level, 'edit')

    def test_06_prnum_to_sortable_num(self):
        """ _prnum_to_sortable returns number given number """
        self.assertEqual(self.dbh._prnum_to_sortable('1234'), 1234)

    def test_07_prnum_to_sortable_scoped(self):
        """ _prnum_to_sortable works for scoped numbers """
        self.assertEqual(self.dbh._prnum_to_sortable('1234-1'), 1234001)

    def test_08_numeric_sortable(self):
        """ _numeric_sortable parses correctly """
        self.assertEqual(self.dbh._numeric_sortable('8.5R1.3'), (8, 5, 1, 3))
        self.assertEqual(self.dbh._numeric_sortable('1234, 5432'), (1234, 5432))
        self.assertEqual(self.dbh._numeric_sortable('fred1'), (1,))
        self.assertEqual(self.dbh._numeric_sortable('fred'), 'fred')


class T02_Query(unittest.TestCase):
    """ query() method. """

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        self.db = Database(self.server, 'testdb', self.conn)
        self.dbh = self.db.get_handle('user', 'pass', self.conn)
        self.conn.rset = self.my_rset
        self.rset_called = False
        self.conn.expr = self.my_expr
        self.expr = ''
        self.conn.qfmt = self.my_qfmt
        self.qfmt = ''
        self.conn.quer = self.my_quer
        self.tqfmt = ''
        self.tqfmt_fname = ''
        self.conn.tqfmt = self.my_tqfmt
        self.db.build_format = self.my_build_format
        self.bf_fnames = []
        self.bf_tfield = []
        self.parse = False
        self.quer_out = []
        self.test_param = ''

    def my_rset(self):
        self.rset_called = True
        return 'Ok.'

    def my_qfmt(self, format):
        self.qfmt = format
        return 'Ok.'

    def my_tqfmt(self, field_name, format):
        self.tqfmt = format
        self.tqfmt_fname = field_name
        return 'Ok.'

    def my_build_format(self, field_names, table_field=None):
        self.bf_fnames.append(field_names)
        self.bf_tfield.append(table_field)
        return 'fred'

    def my_expr(self, expr):
        self.expr = expr
        return 'Ok.'

    def my_quer(self, prs='', parse=False):
        self.parse = parse
        return self.quer_out

    def test_01_raises_empty_expr(self):
        """ Raises on empty expr """
        self.assertRaises(gnats.GnatsException, self.dbh.query, '', ['number'])

    def test_02_raises_bad_sort_field(self):
        """ Raises on non-existent sort field """
        self.assertRaises(gnats.InvalidFieldNameException, self.dbh.query, 'x',
                          field_names='enum-fld', sort=(('blah', 'asc',),))

    def test_03_raises_unrequested_sort_field(self):
        """ Raises if sort field not in field list """
        self.assertRaises(gnats.GnatsException, self.dbh.query, 'x',
                          field_names='enum-fld', sort=(('synopsis', 'asc',),))

    def test_04_raises_bad_sort_dir(self):
        """ Raises if sort direction not asc/desc """
        self.assertRaises(gnats.GnatsException, self.dbh.query, 'x',
                          field_names='enum-fld', sort=(('synopsis', 'foo',),))

    def test_05_calls_rset(self):
        """ Calls RSET """
        self.dbh.query('expr', 'enum-fld')
        self.assertTrue(self.rset_called)

    def test_06_fields_passed_format(self):
        """ correct fields are passed to db.build_format """
        self.dbh.query('expr', 'enum-fld')
        self.assertEquals(self.bf_fnames, [['enum-fld']])
        self.assertEquals(self.qfmt, 'fred')
        self.dbh.query('expr', ['enum-fld', 'synopsis'])
        self.assertEquals(self.bf_fnames,
                          [['enum-fld'], 'enum-fld synopsis'.split()])
        self.assertEquals(self.qfmt, 'fred')

    def test_07_calls_expr(self):
        """ Calls EXPR """
        self.dbh.query('field="value"', 'enum-fld')
        self.assertEqual(self.expr, 'field="value"')

    def test_07_calls_quer_parsed(self):
        """ Calls quer(parsed=True) """
        self.dbh.query('field="value"', 'enum-fld')
        self.assertTrue(self.parse)

    # ['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified']
    results = [
        ['1', 'foo1', 'cat3', 'analyzed', '2008-07-07'],
        ['4', 'foo2', 'cat1', 'analyzed', '2008-02-02'],
        ['6', 'foo3', 'cat4', 'open', '2007-09-09'],
        ['2', 'foo4', 'cat2', 'closed', '2008-02-02'],
    ]

    def test_08_unsorted_default(self):
        """ Results unsorted (gnatsd-natural order) by default """
        self.quer_out = self.results
        res = self.dbh.query('expr',
            ['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['1', '4', '6', '2'])

    def test_09_results_right_size(self):
        """ Results rows correct size """
        self.quer_out = self.results
        res = self.dbh.query('expr',
            ['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        lens = [len(r) for r in res]
        self.assertEquals(lens, [5, 5, 5, 5])

    def test_10_results_cols_correct(self):
        """ Results columns in correct order """
        self.quer_out = self.results
        res = self.dbh.query('expr',
            ['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        self.assertEquals(res[0], ['1', 'foo1', 'cat3', 'analyzed', '2008-07-07'])

    def test_11_sort_enum_asc(self):
        """ Results sorting by enum asc """
        self.quer_out = self.results
        res = self.dbh.query('expr', sort=(('enum-fld', 'asc'), ('number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['4', '2', '1', '6'])

    def test_12_sort_enum_desc(self):
        """ Results sorting by enum desc """
        self.quer_out = self.results
        res = self.dbh.query('expr', sort=(('enum-fld', 'desc'), ('number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['6', '1', '2', '4'])

    def test_13_sort_text_asc(self):
        """ Results sorting by text asc """
        self.quer_out = self.results
        res = self.dbh.query('expr', sort=(('synopsis', 'asc'), ('number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['1', '4', '6', '2'])

    def test_14_sort_text_desc(self):
        """ Results sorting by text desc """
        self.quer_out = self.results
        res = self.dbh.query('expr', sort=(('synopsis', 'desc'), ('number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['2', '6', '4', '1'])

    def test_15_sort_text_enum(self):
        """ Results sorting by text desc, enum asc """
        self.quer_out = self.results
        res = self.dbh.query('expr',
            sort=(('scoped-enum-fld', 'asc'), ('synopsis', 'desc'), ('number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['6', '4', '1', '2'])

    def test_16_sort_date_text(self):
        """ Results sorting by date desc, text asc """
        self.quer_out = self.results
        res = self.dbh.query('expr',
            sort=(('last-modified', 'desc'), ('synopsis', 'asc'), ('number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['1', '4', '2', '6'])

    def test_17_sort_number_asc(self):
        """ Results sorting by number asc """
        self.quer_out = self.results
        res = self.dbh.query('expr',
            sort=(('number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['1', '2', '4', '6'])

    def test_18_sort_number_desc(self):
        """ Results sorting by number desc """
        self.quer_out = self.results
        res = self.dbh.query('expr',
            sort=(('number', 'desc'),),
            field_names=['number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['6', '4', '2', '1'])

    # ['number', 'synopsis', 'enum-fld',]
    scoped_results = [
        ['1-1', 'foo1', 'cat3',],
        ['4-1', 'foo1', 'cat1',],
        ['6-1', 'foo1', 'cat4',],
        ['1-2', 'foo4', 'cat2',],
    ]

    def test_19_sort_number_scoped_desc(self):
        """ Sorting with scoped PRs, number desc """
        self.quer_out = self.scoped_results
        res = self.dbh.query('expr',
            sort=(('number', 'desc'),),
            field_names=['number', 'synopsis', 'enum-fld'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['6-1', '4-1', '1-2', '1-1'])

    def test_20_sort_number_scoped_asc(self):
        """ Sorting with scoped PRs, number asc """
        self.quer_out = self.scoped_results
        res = self.dbh.query('expr',
            sort=(('number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['1-1', '1-2', '4-1', '6-1'])

    def test_21_sort_text_desc_number_scoped_asc(self):
        """ Sorting with scoped PRs, text desc, number asc """
        self.quer_out = self.scoped_results
        res = self.dbh.query('expr',
            sort=(('synopsis', 'desc'), ('number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['1-2', '1-1', '4-1', '6-1'])

    def test_22_sort_text_asc_number_scoped_asc(self):
        """ Sorting with scoped PRs, text asc, number asc """
        self.quer_out = self.scoped_results
        res = self.dbh.query('expr',
            sort=(('synopsis', 'asc'), ('number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['1-1', '4-1', '6-1', '1-2'])

    def test_24_sort_builtinfield_number(self):
        """ Sorting on builtinfield:number """
        self.quer_out = self.scoped_results
        res = self.dbh.query('expr',
            sort=(('synopsis', 'asc'), ('builtinfield:number', 'asc'),),
            field_names=['number', 'synopsis', 'enum-fld'])
        order = [r[0] for r in res]
        self.assertEquals(order, ['1-1', '4-1', '6-1', '1-2'])

    def test_25_builtinfield_number_results(self):
        """ Request builtinfield:number in results """
        self.quer_out = self.results
        res = self.dbh.query('expr',
        ['builtinfield:number', 'synopsis', 'enum-fld', 'scoped-enum-fld', 'last-modified'])
        self.assertEquals(res[0], ['1', 'foo1', 'cat3', 'analyzed', '2008-07-07'])

    def my_numeric_sortable(self, val):
        self.test_param = val
        raise TestExc

    def test_26_numeric_sort(self):
        """ Calls _numeric_sortable when sorting on a numeric sort field """
        self.dbh._numeric_sortable = self.my_numeric_sortable
        self.quer_out = self.results
        self.db.fields['synopsis'].sorting = 'numeric'
        self.assertRaises(TestExc, self.dbh.query, 'expr',
              ['builtinfield:number', 'synopsis', 'enum-fld', 'scoped-enum-fld',
               'last-modified'], (('synopsis', 'asc'),))
        self.assertEqual(self.test_param, 'foo1')

    def test_27_raises_tfield_sort(self):
        """ Raises when table-field in sort """
        try:
            self.dbh.query('expr', ['change-log'], sort=(('change-log', 'asc'),))
            self.fail("Didn't raise as expected")
        except gnats.GnatsException, e:
            self.assertEquals(e.message, "Sorting on 'table' fields is "
                              "not supported.")

    def test_28_fetch_tfield_string(self):
        """ Fetch table-field as string """
        self.dbh.query('expr', 'change-log')
        self.assertEquals(self.bf_fnames, [['change-log']])
        self.assertEquals(self.qfmt, 'fred')

    def test_28_fetch_tfield_parsed_all(self):
        """ Fetch table-field as parsed values (table_cols=all) """
        self.dbh.query('expr', 'change-log', table_cols="all")
        self.assertEquals(self.bf_fnames, [['change-log'], ['row-id',
            'old-value', 'new-value',
            'username', 'change-reason',
            'datetime']])
        self.assertEquals(self.qfmt, 'fred')
        self.assertEquals(self.tqfmt, 'fred')


class T03_Get_pr(unittest.TestCase):
    """ get_pr() and related methods. """

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        self.db = Database(self.server, 'testdb', self.conn)
        self.dbh = self.db.get_handle('user', 'pass', self.conn)
        self.conn.rset = self.my_rset
        self.rset_called = False
        self.conn.qfmt = self.my_qfmt
        self.qfmt = ''
        self.conn.tqfmt = self.my_tqfmt
        self.tqfmt = ''
        self.tqfmt_fname = ''
        self.conn.quer = self.my_quer
        self.parse = False
        self.prnum = []
        self.db.build_format = self.my_build_format
        self.fnames = []
        self.bf_tfield = []
        self.pr_fields = []
        self.table_cols = []
        self.dbh.old_get_pr_fields = self.dbh._get_pr_fields
        self.dbh._get_pr_fields = self.my_get_pr_fields
        self.vtc_cols = ''
        self.vtc_fnames = ''
        self.vtc_out = ''
        self.old_validate_table_columns = self.dbh._validate_table_columns
        self.dbh._validate_table_columns = self.my_validate_table_columns

    def my_rset(self):
        self.rset_called = True
        return 'Ok.'

    def my_qfmt(self, format):
        self.qfmt = format
        return 'Ok.'

    def my_tqfmt(self, field_name, format):
        self.tqfmt = format
        self.tqfmt_fname = field_name
        return 'Ok.'

    def my_quer(self, prs='', parse=False):
        self.parse = parse
        self.prnum = prs
        return 'boo'

    def my_build_format(self, field_names, table_field=None):
        self.fnames.append(field_names)
        self.bf_tfield.append(table_field)
        return 'fred'

    def my_get_pr_fields(self, prnum, field_names, table_cols=None):
        self.fnames.append(field_names)
        self.prnum.append(prnum)
        self.table_cols.append(table_cols)
        return self.pr_fields.pop()

    def my_validate_table_columns(self, table_cols, field_names=None):
        self.vtc_cols = table_cols
        self.vtc_fnames = field_names
        return self.vtc_out

    def test_001_format_query(self):
        """ _format_query no table_cols """
        self.dbh._format_query('x', None)
        self.assertEqual(self.fnames, ['x'])
        self.assertEqual(self.qfmt, 'fred')
        self.assertEqual(self.tqfmt_fname, '')
        self.assertEqual(self.bf_tfield, [None])

    def test_002_format_query_table_cols(self):
        """ _format_query with table_cols """
        self.dbh._format_query('x', {'y':['z'],})
        self.assertEqual(self.fnames, ['x', ['z'],])
        self.assertEqual(self.qfmt, 'fred')
        self.assertEqual(self.tqfmt, 'fred')
        self.assertEqual(self.tqfmt_fname, 'y')
        self.assertEqual(self.bf_tfield, [None, 'y'])

    def test_01_get_pr_fields(self):
        """ _get_pr_fields() makes the right calls """
        out = self.dbh.old_get_pr_fields('100', #IGNORE:E1101
                                         ['enum-fld', 'synopsis'])
        self.assertEqual(self.fnames, [['enum-fld', 'synopsis']])
        self.assertTrue(self.rset_called)
        self.assertEqual(self.qfmt, 'fred')
        self.assertTrue(self.parse)
        self.assertEqual(self.prnum, '100')
        self.assertEqual(out, 'boo')

    def test_02_raises_no_prnum(self):
        """ Raises with no prnum """
        self.assertRaises(gnats.GnatsException, self.dbh.get_pr, '', ['foo'])

    def test_02a_raises_no_fields(self):
        """ Raises with no field_names """
        self.assertRaises(gnats.GnatsException, self.dbh.get_pr, '1', '')

    def test_03_raises_bad_fields(self):
        """ Raises when given invalid field_names """
        self.assertRaises(gnats.InvalidFieldNameException,
                          self.dbh.get_pr, '1', ['foo'])

    def test_04_raises_bad_field_names(self):
        """ Invalid field_names exc includes names of bad fields """
        try:
            self.dbh.get_pr('1', ['foo', 'bar'])
            self.fail("Invalid fields didn't raise an exception.")
        except gnats.InvalidFieldNameException, g:
            self.assertTrue(g.message.find('foo') > -1) #IGNORE:E1101
            self.assertTrue(g.message.find('bar') > -1) #IGNORE:E1101

    def test_05_raises_no_pr(self):
        """ Raises when PR not found """
        self.pr_fields = [None]
        self.assertRaises(gnats.PRNotFoundException, self.dbh.get_pr, '1', ['number'])

    def test_06_one_field(self):
        """ Retrieve one field """
        self.pr_fields = [[['fred']]]
        self.vtc_out = {}
        self.assertEqual(self.dbh.get_pr('1', ['enum-fld']),
                         {'enum-fld':'fred'})
        self.assertEqual(self.fnames, [['enum-fld']])
        self.assertEqual(self.prnum, ['1'])
        self.assertEqual(self.table_cols, [{},])

    def test_07_two_fields(self):
        """ Retrieve two fields """
        self.pr_fields = [[['fred', 'joe']]]
        self.vtc_out = {}
        self.assertEqual(self.dbh.get_pr('1', ['enum-fld', 'synopsis']),
                         {'enum-fld':'fred', 'synopsis':'joe'})
        self.assertEqual(self.fnames, [['enum-fld', 'synopsis']])
        self.assertEqual(self.prnum, ['1'])
        self.assertEqual(self.table_cols, [{},])

    def test_08_scoped_only(self):
        """ Retrieve a scoped field """
        self.pr_fields = [[['1', 'fred']]]
        self.vtc_out = {}
        self.assertEqual(self.dbh.get_pr('1', ['scoped-enum-fld']),
                         {'identifier': [('1', {'scoped-enum-fld':'fred',
                                                'scope:identifier': '1'})]})
        self.assertEqual(self.fnames, [['scope:identifier', 'scoped-enum-fld']])
        self.assertEqual(self.prnum, ['1'])
        self.assertEqual(self.table_cols, [None,])

    def test_09_two_scopes(self):
        """ Retrieve a scoped field with two scopes """
        self.pr_fields = [[['2', 'joe'], ['1', 'fred']]]
        self.vtc_out = {}
        self.assertEqual(self.dbh.get_pr('1', ['scoped-enum-fld']),
                         {'identifier': [('1', {'scoped-enum-fld':'fred',
                                                'scope:identifier': '1'}),
                                         ('2', {'scoped-enum-fld':'joe',
                                                'scope:identifier': '2'})]})
        self.assertEqual(self.fnames, [['scope:identifier', 'scoped-enum-fld']])
        self.assertEqual(self.prnum, ['1'])
        self.assertEqual(self.table_cols, [None,])

    def test_10_many_fields(self):
        """ Retrieve scoped and non-scoped fields """
        self.pr_fields = [[['1', 'fred']], [['joe']]]
        self.vtc_out = {}
        self.assertEqual(self.dbh.get_pr('1', ['synopsis', 'scoped-enum-fld']),
                         {'synopsis':'joe',
                          'identifier': [('1', {'scoped-enum-fld':'fred',
                                                'scope:identifier': '1'})]})
        self.assertEqual(self.fnames, [['synopsis'],
                                       ['scope:identifier', 'scoped-enum-fld']])
        self.assertEqual(self.prnum, ['1', '1'])
        self.assertEqual(self.table_cols, [{}, None])

    def test_11_scoped_pr_num(self):
        """ Retrieve one scope with scoped PR number """
        self.pr_fields = [[['1', 'fred']], [['joe']]]
        self.vtc_out = {}
        self.assertEqual(self.dbh.get_pr('1-1',
                                         ['synopsis', 'scoped-enum-fld'],
                                         one_scope=True),
                         {'synopsis':'joe',
                          'identifier': [('1', {'scoped-enum-fld':'fred',
                                                'scope:identifier': '1'})]})
        self.assertEqual(self.fnames, [['synopsis'],
                                       ['scope:identifier', 'scoped-enum-fld']])
        self.assertEqual(self.prnum, ['1', '1-1'])
        self.assertEqual(self.table_cols, [{}, None])

    def test_12_scoped_pr_num_all_scopes(self):
        """ Retrieve all scopes with scoped PR number """
        self.pr_fields = [[['1', 'fred'], ['2', 'mary']], [['joe']]]
        self.vtc_out = {}
        self.assertEqual(self.dbh.get_pr('1-1',
                                         ['synopsis', 'scoped-enum-fld'],
                                         one_scope=False),
                         {'synopsis':'joe',
                          'identifier': [('1', {'scoped-enum-fld':'fred',
                                                'scope:identifier': '1'}),
                                         ('2', {'scoped-enum-fld':'mary',
                                                'scope:identifier': '2'})]})
        self.assertEqual(self.fnames, [['synopsis'],
                                       ['scope:identifier', 'scoped-enum-fld']])
        self.assertEqual(self.prnum, ['1', '1'])
        self.assertEqual(self.table_cols, [{}, None])

    def test_13_table_field_string(self):
        """ Retrieve table field as string """
        self.pr_fields = [[['fred', 'joe']]]
        self.assertEqual(self.dbh.get_pr('1', ['enum-fld', 'change-log'],
                                         table_cols=None),
                         {'enum-fld':'fred', 'change-log':'joe'})
        self.assertEqual(self.fnames, [['enum-fld', 'change-log']])
        self.assertEqual(self.prnum, ['1'])
        self.assertEqual(self.table_cols, [None])

    def test_14_table_field_parsed(self):
        """ Retrieve table field parsed into a dict """
        self.pr_fields = [[['fred', 'joe%sjane%sbill%sbarb%s' %
            (codes.COL_SEP, codes.ROW_SEP, codes.COL_SEP, codes.ROW_SEP,)]]]
        self.vtc_out = {'change-log': ['x', 'y']}
        self.assertEqual(self.dbh.get_pr('1', ['enum-fld', 'change-log']),
             {'enum-fld':'fred', 'change-log':[{'x': 'joe', 'y': 'jane'},
                                               {'x': 'bill', 'y': 'barb'}],})
        self.assertEqual(self.fnames, [['enum-fld', 'change-log']])
        self.assertEqual(self.prnum, ['1'])
        self.assertEqual(self.table_cols, [{'change-log': ['x', 'y']}])

    def test_15_table_field_one_parsed(self):
        """ Retrieve specific table field parsed into a dict """
        self.pr_fields = [[['fred', 'joe%sjane%sbill%sbarb%s' %
            (codes.COL_SEP, codes.ROW_SEP, codes.COL_SEP, codes.ROW_SEP,)]]]
        self.vtc_out = {'change-log': ['x', 'y']}
        self.assertEqual(self.dbh.get_pr('1', ['enum-fld', 'change-log'],
                                         table_cols={'change-log': ['x', 'y']}),
             {'enum-fld':'fred', 'change-log':[{'x': 'joe', 'y': 'jane'},
                                               {'x': 'bill', 'y': 'barb'}],})
        self.assertEqual(self.fnames, [['enum-fld', 'change-log']])
        self.assertEqual(self.prnum, ['1'])
        self.assertEqual(self.table_cols, [{'change-log': ['x', 'y']}])


class T04_Edit_pr(unittest.TestCase):
    """ edit_pr() """

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        self.db = Database(self.server, 'testdb', self.conn)
        self.dbh = self.db.get_handle('user', 'pass', self.conn)
        self.edit = self.dbh.edit_pr
        self.conn.edit = self.my_edit
        self.prnum_in = ''
        self.db.unparse_pr = self.my_unparse_pr
        self.unp_in = {}
        self.conn.editaddr = self.my_editaddr
        self.addr_in = ''
        self.dbh.get_pr = self.my_get_pr
        # Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld
        self.curr_pr = {'synopsis': 'foo bar',
               'enum-fld': 'sw-tools',
               'multienum-fld': 'tools',
               'multitext-fld': 'a value',
               'identifier': [(1, {'scoped-enum-fld': 'open'})],}

    def my_edit(self, prnum, pr):
        self.prnum_in = prnum
        return 'Ok.'

    def my_unparse_pr(self, pr):
        self.unp_in = pr
        return 'foo'

    def my_editaddr(self, addr):
        return 'Ok.'

    def my_get_pr(self, prnum, field_names='all'):
        return self.curr_pr

    def test_01_raises_no_pr(self):
        """ Raises if no pr supplied """
        self.assertRaises(gnats.GnatsException, self.edit, 1234, None, 'user')

    def test_02_raises_no_prnum(self):
        """ Raises if no prnum supplied """
        self.assertRaises(gnats.GnatsException, self.edit, '', {1:1}, 'user')

    def test_03_raises_no_user_address(self):
        """ Raises if no user_address supplied """
        self.assertRaises(gnats.GnatsException, self.edit, 1234, {1:1}, '')

    def test_04_calls_editaddr(self):
        """ editaddr is called correctly """
        def ea(addr):
            self.addr_in = addr
            raise TestExc()
        self.conn.editaddr = ea
        self.assertRaises(TestExc, self.edit, 1234, {'synopsis':1}, 'user')
        self.assertEqual(self.addr_in, 'user')

    def test_04a_calls_get_pr(self):
        """ get_pr is called with prnum and writeable fields """
        def gp(prnum, field_names):
            self.prnum_in = prnum
            self.unp_in = field_names
            raise TestExc()
        self.dbh.get_pr = gp
        self.assertRaises(TestExc, self.edit, 1234, {'synopsis':1}, 'user')
        self.assertEqual(self.prnum_in, '1234')
        self.assertEqual(self.unp_in, ['synopsis', 'enum-fld', 'scoped-enum-fld',
                                       'multienum-fld', 'multitext-fld',
                                       'last-modified', 'reply-to:', 'from:',])

    def test_05_checks_last_modified_diff(self):
        """ Raises if last_modified differs """
        self.curr_pr['last-modified'] = 'foo'
        self.assertRaises(gnats.LastModifiedTimeException, self.edit, 1234,
                          {'last-modified': 'bar', 'synopsis':1}, 'user')

    def test_06_checks_last_modified_same(self):
        """ OK if last_modified the same """
        self.curr_pr['last-modified'] = 'bar'
        self.edit(1234, {'last-modified': 'bar', 'synopsis':1}, 'user')
        # The call to edit() will raise if things aren't right...

    def test_07_adds_number(self):
        """ Adds number field to pr dict """
        self.edit(1234, {'synopsis': 'boo'}, 'user')
        self.assertEqual(self.unp_in['number'], '1234')

    def test_07_interleaves_non_scoped(self):
        """ Correctly interleaves non-scoped field data """
        self.edit(1234, {'synopsis': 'boo'}, 'user')
        self.assertEqual(self.unp_in, {'synopsis': 'boo',
               'enum-fld': 'sw-tools',
               'multienum-fld': 'tools',
               'multitext-fld': 'a value',
               'identifier': [(1, {'scoped-enum-fld': 'open'})],
               'number': '1234',})

    def test_08_interleaves_scoped(self):
        """ Correctly interleaves existing scoped field data """
        self.edit(1234, {'identifier': [(1, {'scoped-enum-fld': 'boo'})]}, 'x')
        self.assertEqual(self.unp_in, {'synopsis': 'foo bar',
               'enum-fld': 'sw-tools',
               'multienum-fld': 'tools',
               'multitext-fld': 'a value',
               'identifier': [(1, {'scoped-enum-fld': 'boo'})],
               'number': '1234',})

    def test_09_interleaves_new_scope(self):
        """ Correctly interleaves a new scope """
        self.edit(1234, {'identifier': [(2, {'scoped-enum-fld': 'boo'})]}, 'x')
        self.assertEqual(self.unp_in, {'synopsis': 'foo bar',
               'enum-fld': 'sw-tools',
               'multienum-fld': 'tools',
               'multitext-fld': 'a value',
               'identifier': [(2, {'scoped-enum-fld': 'boo'}),
                              (1, {'scoped-enum-fld': 'open'})],
               'number': '1234',})

    def test_10_envelope_fields(self):
        """ Correctly interleaves envelope fields """
        self.curr_pr['from:'] = 'wow'
        self.edit(1234, {'from:': 'fred'}, 'x')
        self.assertEqual(self.unp_in, {'synopsis': 'foo bar',
               'enum-fld': 'sw-tools',
               'multienum-fld': 'tools',
               'multitext-fld': 'a value',
               'identifier': [(1, {'scoped-enum-fld': 'open'})],
               'number': '1234',
               'from:': 'fred',})

    def test_11_removes_scope(self):
        """ Scope is stripped off the PR number """
        self.edit('1234-1', {'from:': 'fred'}, 'x')
        self.assertEqual(self.prnum_in, '1234')
        def gp(prnum, field_names):
            self.prnum_in = prnum
            self.unp_in = field_names
            raise TestExc()
        self.dbh.get_pr = gp
        self.assertRaises(TestExc, self.edit, '1234-1', {'from:': 'fred'}, 'user')
        self.assertEqual(self.prnum_in, '1234')

    def test_12_honors_really_read_only_non_scoped(self):
        """ Honors _really_read_only flag """
        self.db.fields['synopsis'].read_only = True
        self.edit(1234, {'enum-fld': 'boo'}, 'user')
        self.assertEqual(self.unp_in['synopsis'], 'foo bar')

    def test_13_honors_really_read_only_scoped(self):
        """ Honors _really_read_only flag """
        self.db.fields['scoped-enum-fld'].read_only = True
        self.edit(1234, {'enum-fld': 'boo'}, 'user')
        self.assertEqual(self.unp_in['identifier'][0][1]['scoped-enum-fld'],
                         'open')

    def test_14_skips_table_fields(self):
        """ Skips table-fields when fetching current PR """
        def gp(prnum, field_names):
            self.prnum_in = prnum
            self.unp_in = field_names
            raise TestExc()
        self.dbh.get_pr = gp
        self.db.fields['change-log'].read_only = False
        self.db.fields['change-log']._really_read_only = False
        self.assertRaises(TestExc, self.edit, 1234, {'change-log':'foo'}, 'user')
        self.assertEqual(self.prnum_in, '1234')
        self.assertEqual(self.unp_in, ['synopsis', 'enum-fld', 'scoped-enum-fld',
                                       'multienum-fld', 'multitext-fld',
                                       'last-modified', 'reply-to:', 'from:',])

    def test_15_skips_table_fields(self):
        """ Skips not-really-read-only table-field when filling in from curr PR
        """
        self.db.fields['change-log'].read_only = True
        self.db.fields['change-log']._really_read_only = False
        self.edit(1234, {'synopsis': 'boo'}, 'user')
        self.assertEqual(self.unp_in['synopsis'], 'boo')


class T05_MiscEditMethods(unittest.TestCase):
    """ submit_pr, lock_pr, unlock_pr, append_to_field, replace_field, check_pr
    """

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        self.db = Database(self.server, 'testdb', self.conn)
        self.dbh = self.db.get_handle('user', 'pass', self.conn)
        self.db.unparse_pr = self.my_unparse_pr
        self.unp_in = {}
        self.conn.editaddr = self.my_editaddr
        self.edad_in = ''
        self.testval = None

    def my_unparse_pr(self, pr):
        self.unp_in = pr
        return 'foo'

    def my_editaddr(self, addr):
        self.edad_in = addr
        return 'Ok.'

    def test_01_submit_pr_unparse(self):
        """ submit_pr() calls unparse """
        self.conn.subm = lambda pr, sess: True
        self.dbh.submit_pr('fred')
        self.assertEqual(self.unp_in, 'fred')

    def test_02_submit_pr_subm(self):
        """ submit_pr() calls conn.subm() """
        def subm(pr, sess): #@UnusedVariable
            self.testval = pr
            raise TestExc()
        self.conn.subm = subm
        self.assertRaises(TestExc, self.dbh.submit_pr, 'fred')
        self.assertEqual(self.testval, 'foo')

    def test_03_lock_pr(self):
        """ lock_pr() with session """
        def lockn(prnum, user, pid, sess):
            self.testval = [prnum, user, pid, sess]
            raise TestExc()
        self.conn.lockn = lockn
        self.assertRaises(TestExc, self.dbh.lock_pr, 1234, 'user', 321, 'sess')
        self.assertEqual(self.testval[0], '1234')
        self.assertEqual(self.testval[1], 'user')
        self.assertEqual(self.testval[2], 321)
        self.assertEqual(self.testval[3], 'sess')

    def test_03a_lock_pr(self):
        """ lock_pr() without session """
        def lockn(prnum, user, pid, sess=''):
            self.testval = [prnum, user, pid, sess]
            raise TestExc()
        self.conn.lockn = lockn
        self.assertRaises(TestExc, self.dbh.lock_pr, 1234, 'user', 321)
        self.assertEqual(self.testval[0], '1234')
        self.assertEqual(self.testval[1], 'user')
        self.assertEqual(self.testval[2], 321)
        self.assertEqual(self.testval[3], '')

    def test_03b_lock_pr_scope(self):
        """ lock_pr() with scoped PR number """
        def lockn(prnum, user, pid, sess):
            self.testval = [prnum, user, pid, sess]
            raise TestExc()
        self.conn.lockn = lockn
        self.assertRaises(TestExc, self.dbh.lock_pr, '1234-1', 'user', 321, 'sess')
        self.assertEqual(self.testval[0], '1234')

    def test_04_unlock_pr(self):
        """ unlock_pr() """
        def unlk(prnum):
            self.testval = prnum
            raise TestExc()
        self.conn.unlk = unlk
        self.assertRaises(TestExc, self.dbh.unlock_pr, 1234)
        self.assertEqual(self.testval, '1234')

    def test_04a_unlock_pr_scope(self):
        """ unlock_pr() with scoped PR number """
        def unlk(prnum):
            self.testval = prnum
            raise TestExc()
        self.conn.unlk = unlk
        self.assertRaises(TestExc, self.dbh.unlock_pr, '1234-1')
        self.assertEqual(self.testval, '1234')

    def test_05_append_to_field(self):
        """ append_to_field() """
        def foo(prnum, fname, value, scope, sess):
            self.testval = [prnum, fname, value, scope, sess]
            raise TestExc()
        self.conn.appn = foo
        self.assertRaises(TestExc, self.dbh.append_to_field, 1234, 'field',
                          'value', 'user', 1, 'sess')
        self.assertEqual(self.edad_in, 'user')
        self.assertEqual(self.testval[0], '1234')
        self.assertEqual(self.testval[1], 'field')
        self.assertEqual(self.testval[2], 'value')
        self.assertEqual(self.testval[3], 1)
        self.assertEqual(self.testval[4], 'sess')

    def test_05a_append_to_field_scoped(self):
        """ append_to_field() with scoped PR number """
        def foo(prnum, fname, value, scope, sess):
            self.testval = [prnum, fname, value, scope, sess]
            raise TestExc()
        self.conn.appn = foo
        self.assertRaises(TestExc, self.dbh.append_to_field, '12345-1', 'field',
                          'value', 'user', 1, 'sess')
        self.assertEqual(self.testval[0], '12345')

    def test_06_replace_field(self):
        """ replace_field() """
        def foo(prnum, fname, value, scope, sess):
            self.testval = [prnum, fname, value, scope, sess]
            raise TestExc()
        self.conn.repl = foo
        self.assertRaises(TestExc, self.dbh.replace_field, 1234, 'field',
                          'value', 'user', 1, 'sess')
        self.assertEqual(self.edad_in, 'user')
        self.assertEqual(self.testval[0], '1234')
        self.assertEqual(self.testval[1], 'field')
        self.assertEqual(self.testval[2], 'value')
        self.assertEqual(self.testval[3], 1)
        self.assertEqual(self.testval[4], 'sess')

    def test_06a_replace_field_scoped(self):
        """ replace_field() with scoped PR number """
        def foo(prnum, fname, value, scope, sess):
            self.testval = [prnum, fname, value, scope, sess]
            raise TestExc()
        self.conn.repl = foo
        self.assertRaises(TestExc, self.dbh.replace_field, '1234-1', 'field',
                          'value', 'user', 1, 'sess')
        self.assertEqual(self.testval[0], '1234')

    def test_07_check_pr_unparse(self):
        """ check_pr() calls unparse """
        self.conn.chek = lambda pr, initial: True
        self.dbh.check_pr('fred')
        self.assertEqual(self.unp_in, 'fred')

    def test_08_check_pr_chek(self):
        """ check_pr() calls conn.chek() """
        def chek(pr, initial): #@UnusedVariable
            self.testval = pr
            raise TestExc()
        self.conn.chek = chek
        self.assertRaises(TestExc, self.dbh.check_pr, 'fred')
        self.assertEqual(self.testval, 'foo')


classes = (
          T01_MetadataAndUtilityMethods,
          T02_Query,
          T03_Get_pr,
          T04_Edit_pr,
          T05_MiscEditMethods,
         )

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    suites = []
    for cl in classes:
        suites.append(unittest.makeSuite(cl, 'test'))
    runner.run(unittest.TestSuite(suites))
