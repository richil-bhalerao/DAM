#!/usr/bin/python
"""
Unit tests for gnats Database class

Dirk Bergstrom, dirk@juniper.net, 2008-04-24

Copyright (c) 2008, Juniper Networks, Inc.
All rights reserved.
"""
import unittest

# Shut up logging during the tests
import logging
logging.disable(logging.FATAL)

import gnats
from gnats import Database, DatabaseHandle, GnatsException
from gnats.database import Field, EnumField

class FakeServerConnectionForDB(object):
    """ Passed to Database's constructor to get a db object for testing. """

    def __init__(self, server):
        self.server = server
        self._ftyp_out = [
             'Integer Text Text Text Multitext Date'.split(),
             'Integer Text Enum Enum MultiEnum Multitext Table Date'.split(),]
        self._inputdefault_out = [
             '::::::'.split(':'),
             '-1::somecategory:open:value::::'.split(':'),]
        self._flags_out = [
              '::::::'.split(':'),
              """readonly
textsearch required
requireChangeReason
multivalued textsearch requireChangeReason
req-cond
allowAnyValue
readonly
readonly""".split('\n'),]
        self._axes_out = ["""






""".split('\n'),
"""


Identifier



""".split('\n'),]
        self._desc_out = ["""Change-Log row
Old value
New value
User name
Change reason
Change date""".split('\n'),
"""PR Number field
Synopsis field
Category field
State field
Platform field
Description field
Change-Log field
Last-Modified field""".split('\n'),]

    def chdb(self, db, user='', passwd='', userpass=None):
        return 'edit'

    def dbdesc(self, dbname): #IGNORE:E0202
        return "Fake Database"

    FIELDNAMES = 'Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld ' \
                 'Multitext-fld Change-Log Last-Modified'
    _lists = {
              'fieldnames':FIELDNAMES.split(),
              'initialinputfields':'Synopsis Enum-fld Multitext-fld'.split()
              }
    def list(self, list_type):
        return list(self._lists[list_type])

    def ftyp(self, names):
        return self._ftyp_out.pop()

    def inputdefault(self, names):
        return self._inputdefault_out.pop()

    def fieldflags(self, names):
        return self._flags_out.pop()

    def fdsc(self, names):
        return self._desc_out.pop()

    _fvlds = {
              'enum-fld*':"""cat1:c11:c12:c13:c14:c15:c16
cat2:c22:c22:c23:c24:c25:c26
cat3:c32:c32:c33:c34:c35:c36
cat4:c42:c42:c43:c44:c45:c46""".split('\n'),
              'scoped-enum-fld*':"""open::Default state
analyzed:analyzed:Problem examined
closed:closed:PR shut""".split('\n'),
              'multienum-fld':'product1 product2 product3 product4'.split(),
              }
    def fvld(self, name, *subfield_args):
        key = '%s%s' % (name, ''.join(subfield_args))
        return list(self._fvlds[key])

    _ftypinfos = {
                  'multienum-fld:separators':["':|'"],
                  'enum-fld:subfields': """category description owner notify
                      group group-owner""".split(),
                  'responsible:subfields': "username fullname alias".split(),
                  'scoped-enum-fld:subfields': "state type description".split(),
                  'submitter-id:subfields': """submitter fullname type
                      rtime notify""".split(),
                  'change-log:columns': """Row-Id Old-Value New-Value Username
                      Change-Reason Datetime""".split()
                  }
    def ftypinfo(self, field, prop):
        fp = '%s:%s' % (field, prop)
        if fp == 'multienum-fld:subfields':
            raise gnats.GnatsException("boo", code='435')
        return list(self._ftypinfos[fp])

    def cfgt(self): #IGNORE:E0202
        return u'1000'


class T01_DatabaseMetadata(unittest.TestCase):
    """ Test Database class metadata """

    def setUp(self):
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        self.db = Database(self.server, 'testdb', self.conn)

    def test_01_name(self):
        """ Database name """
        self.assertEqual(self.db.name, 'testdb')

    def test_02_description(self):
        """ description """
        self.assertEqual(self.db.description, 'Fake Database')

    def test_03_cfgt(self):
        """ last_config_time """
        self.assertEqual(self.db.last_config_time, u'1000')

    def test_04_ordered_field_names(self):
        """ ordered_field names """
        fnames = ' '.join([f.name for f in self.db.ordered_fields])
        self.assertEqual(fnames, self.conn.FIELDNAMES)

    def test_08_initial_entry(self):
        """ initial_entry_fields """
        self.assertEqual([f.lcname for f in self.db.initial_entry_fields],
                         'synopsis enum-fld multitext-fld from:'.split())

    def test_09_number_field_is_first(self):
        """ First db field is number_field """
        self.assertEqual(self.db.number_field.name, 'Number')

    def test_10_builtinfield_number(self):
        """ fields has key builtinfield:number """
        self.assertEqual(self.db.fields['builtinfield:number'],
                         self.db.fields['number'])

    def test_11_number_field(self):
        """ number_field is builtinfield:number """
        self.assertEqual(self.db.number_field,
                         self.db.fields['builtinfield:number'])

    def test_12_builtins(self):
        """ Check for builtinfield:synopsis and last-modified """
        self.assertEqual(self.db.fields['builtinfield:synopsis'],
                         self.db.fields['synopsis'])
        self.assertEqual(self.db.fields['builtinfield:last-modified'],
                         self.db.fields['last-modified'])

    def test_13_callback(self):
        """ Callback called after _get_metadata() """
        def cb(db):
            cb.dbin = db
        self.db.post_metadata_callback = cb
        # "Refresh" the conn, so that metadata can run again
        self.conn = FakeServerConnectionForDB(self.server)
        self.db.last_config_time = 987
        self.db._get_metadata(self.conn)
        self.assertEqual(cb.dbin, self.db)
        
    def test_14_update_metadata_no_refresh(self):
        """ update_metadata method doesn't refresh if cached data good. """
        def gm(conn):
            gm.c = conn
        gm.c = None
        self.db._get_metadata = gm 
        self.conn = FakeServerConnectionForDB(self.server)
        self.db.update_metadata(self.conn)
        self.assertEqual(gm.c, None)
        
    def test_15_update_metadata_refresh(self):
        """ update_metadata method refreshes if cached data stale. """
        def gm(conn):
            gm.c = conn
        gm.c = None
        self.db._get_metadata = gm 
        self.conn = FakeServerConnectionForDB(self.server)
        self.db.last_config_time = 987
        self.db.update_metadata(self.conn)
        self.assertEqual(gm.c, self.conn)


class T02_FieldMetadata(unittest.TestCase):
    """ Check field metadata """

    def setUp(self):
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        self.db = Database(self.server, 'testdb', self.conn)
        self.fld = self.db.fields['synopsis']

    # 'Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified'
    def test_01_name(self):
        """ Field name """
        self.assertEqual(self.fld.name, 'Synopsis')

    def test_02_description(self):
        """ description """
        self.assertEqual(self.fld.description, 'Synopsis field')

    def test_03_default(self):
        """ default """
        self.assertEqual(self.db.fields['enum-fld'].default, 'somecategory')

    def test_04_ftype(self):
        """ field type """
        self.assertEqual(self.db.fields['multienum-fld'].ftype, 'multienum')
        self.assertEqual(self.db.fields['synopsis'].ftype, 'text')

    def test_05_read_only(self):
        """ read only flag """
        self.assertTrue(self.db.fields['last-modified'].read_only)
        self.assertFalse(self.db.fields['synopsis'].read_only)

    def test_05a_really_read_only(self):
        """ really read only flag """
        self.db.fields['synopsis'].read_only = True
        self.assertTrue(self.db.fields['synopsis'].read_only)
        self.assertFalse(self.db.fields['synopsis']._really_read_only)

    def test_06_required(self):
        """ required flag """
        self.assertTrue(self.db.fields['synopsis'].required)
        self.assertFalse(self.db.fields['multitext-fld'].required)

    def test_07_change_reason(self):
        """ require change reason flag """
        self.assertTrue(self.db.fields['scoped-enum-fld'].require_change_reason)
        self.assertFalse(self.db.fields['synopsis'].require_change_reason)

    def test_08_multivalued(self):
        """ multivalued flag """
        self.assertTrue(self.db.fields['scoped-enum-fld'].multi_valued)
        self.assertFalse(self.db.fields['enum-fld'].multi_valued)

    def test_09_textsearch(self):
        """ textsearch flag """
        self.assertTrue(self.db.fields['synopsis'].text_search)
        self.assertFalse(self.db.fields['last-modified'].text_search)

    def test_10_initial(self):
        """ initial flag """
        self.assertTrue(self.db.fields['synopsis'].initial)
        self.assertFalse(self.db.fields['scoped-enum-fld'].initial)

    def test_11_req_cond(self):
        """ req-cond flag """
        self.assertTrue(self.db.fields['multienum-fld'].req_cond)
        self.assertFalse(self.db.fields['synopsis'].req_cond)

    def test_12_allow_any_value(self):
        """ allowAnyValue flag """
        self.assertTrue(self.db.fields['multitext-fld'].allow_any_value)
        self.assertFalse(self.db.fields['synopsis'].allow_any_value)

    def test_13_classes(self):
        """ fields have correct class """
        self.assertTrue(isinstance(self.db.fields['synopsis'], Field))
        self.assertTrue(isinstance(self.db.fields['enum-fld'], EnumField))

    def test_14_sorting(self):
        """ Fields have correct sorting strategies """
        self.assertEqual(self.db.fields['number'].sorting, 'integer')
        self.assertEqual(self.db.fields['scoped-enum-fld'].sorting, 'enum')
        self.assertEqual(self.db.fields['multienum-fld'].sorting, 'enum')
        self.assertEqual(self.db.fields['synopsis'].sorting, 'alpha')
        self.assertEqual(self.db.fields['multitext-fld'].sorting, 'alpha')
        self.assertEqual(self.db.fields['last-modified'].sorting, 'alpha')
        self.assertEqual(self.db.fields['from:'].sorting, 'alpha')


class T03_EnumField(unittest.TestCase):
    """ EnumField tests """

    def setUp(self):
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        self.db = Database(self.server, 'testdb', self.conn)
        self.enum = self.db.fields['enum-fld']
        self.multi = self.db.fields['multienum-fld']

    def tearDown(self):
        gnats.metadata_level = gnats.FULL_METADATA

    def test_1_values(self):
        """ values """
        self.assertEqual(self.enum.values, ['cat1', 'cat2', 'cat3', 'cat4'])

    def test_2_sort_keys(self):
        """ sort_keys """
        self.assertEqual(self.enum.sort_keys['cat1'], 0)
        self.assertEqual(self.multi.sort_keys['product2'], 1)

    def test_3_separators(self):
        """ separators """
        self.assertEqual(self.multi.separators, ':|')

    def test_4_default_separator(self):
        """ default_separator """
        self.assertEqual(self.multi.default_separator, ':')

    def test_5_list_values(self):
        """ list_values """
        self.assertEqual(self.db.fields['scoped-enum-fld'].list_values(),
                         ['open', 'analyzed', 'closed'])

    def test_06_values_dict(self):
        """ subfield dict values """
        fld = self.db.fields['enum-fld']
        self.assertEqual(len(fld.values), 4)
        self.assertEqual(len(fld.values_dict), 4)
        self.assertEqual(fld.values_dict['cat1'],
                         {'owner': 'c12', 'group-owner': 'c15', 'group': 'c14',
                          'description': 'c11', 'notify': 'c13',
                          'category': 'cat1'})

    def test_07_load_metadata(self):
        """ load_metadata method """
        gnats.metadata_level = gnats.NO_ENUM_METADATA
        # "Refresh" the conn, so that metadata can run again
        self.conn = FakeServerConnectionForDB(self.server)
        self.db.last_config_time = 987
        self.db._get_metadata(self.conn)
        enum = self.db.fields['enum-fld']
        self.assertEqual(len(enum.values), 0)
        self.conn = FakeServerConnectionForDB(self.server)
        enum.load_enum_values(self.conn)
        self.assertEqual(len(enum.values), 4)


class T03a_TableField(unittest.TestCase):
    """ TableField tests """

    def setUp(self):
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        self.db = Database(self.server, 'testdb', self.conn)
        self.tfield = self.db.fields['change-log']

    def test_01_ordered_columns(self):
        """ ordered columns """
        self.assertEqual(len(self.tfield.ordered_columns), 6)
        self.assertEqual(self.tfield.ordered_columns[0].lcname,
                         'change-log.row-id')

    def test_02_column_type(self):
        """ column type """
        self.assertEqual(self.tfield.ordered_columns[1].ftype, 'text')

    def test_03_column_description(self):
        """ column description """
        self.assertEqual(self.tfield.ordered_columns[2].description, 'New value')

    def test_04_column_description(self):
        """ column description """
        self.assertEqual(self.tfield.ordered_columns[2].description, 'New value')

    def test_05_column_by_name(self):
        """ column by name """
        self.assertEqual(self.tfield.ordered_columns[2],
                         self.tfield.columns['new-value'])

    def test_06_column_by_qualified_name(self):
        """ column by qualified name """
        self.assertEqual(self.tfield.ordered_columns[2],
                         self.tfield.columns['change-log.new-value'])

    def test_07_column_unqualified_name_attr(self):
        """ column has unqualified_name attribute """
        self.assertEqual(self.tfield.ordered_columns[2].unqualified_name,
                         'new-value')

    def test_08_column_display_name(self):
        """ column name attribute is unqualified, capitalized name """
        self.assertEqual(self.tfield.ordered_columns[2].name,
                         'New-Value')


class T04_DatabaseMethods(unittest.TestCase):
    """ Test Database utility methods """

    def setUp(self):
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        self.db = Database(self.server, 'testdb', self.conn)

    def test_01_get_handle(self):
        """ get_handle returns DatabaseHandle """
        self.assertTrue(isinstance(self.db.get_handle('user', 'pass', self.conn),
                        DatabaseHandle))

    def test_02_get_handle_doesnt_refresh(self):
        """ get_handle uses cached metadata when not expired """
        # Change the dbdesc method to return something we can check
        self.conn.dbdesc = lambda __: 'changed database'
        self.db.get_handle('user', 'pass', self.conn)
        self.assertNotEquals(self.db.description, 'changed database')

    def test_03_get_handle_refreshes(self):
        """ get_handle refreshes metadata when expired """
        # "Refresh" the conn, so that metadata can run again
        conn = FakeServerConnectionForDB(self.server)
        # change the config time returned by conn, which should trigger refresh
        conn.cfgt = lambda: u'10000'
        # Change the dbdesc method to return something we can check
        conn.dbdesc = lambda __: 'changed database'
        self.assertEquals(self.db.last_config_time, u'1000')
        self.db.get_handle('user', passwd='pass', conn=conn)
        self.assertEquals(self.db.description, 'changed database')
        self.assertEquals(self.db.last_config_time, u'10000')

    def test_03a_no_cfgt(self):
        """ get_handle refresh works when CFGT not implemented """
        # "Refresh" the conn, so that metadata can run again
        conn = FakeServerConnectionForDB(self.server)
        # change the config time returned by conn, which should trigger refresh
        def fake_cfgt():
            raise gnats.GnatsException('boo')
        conn.cfgt = fake_cfgt
        # Change the dbdesc method to return something we can check
        conn.dbdesc = lambda __: 'changed database'
        self.db.get_handle('user', passwd='pass', conn=conn)
        self.assertEquals(self.db.description, 'changed database')

    def test_04_list_fields(self):
        """ list_fields """
        flist = self.db.list_fields()
        self.assertEqual(len(flist), 8)
        self.assertEqual(flist[1].name, 'Synopsis')
        self.assertEqual(flist[2].ftype, 'enum')

    def test_05_build_format(self):
        """ build_format """
        self.assertEqual(self.db.build_format(['synopsis', 'enum-fld']),
                         '"%s\037%s\036" synopsis enum-fld')

    def test_06_build_format_builtin(self):
        """ build_format with builtinfield:number """
        self.assertEqual(self.db.build_format(['builtinfield:number',
                                               'enum-fld']),
                 '"%s\037%s\036" builtinfield:number enum-fld')

    def test_07_build_format_date(self):
        """ build_format with date """
        self.assertEqual(self.db.build_format(['synopsis', 'last-modified']),
            '"%s\037%{%Y-%m-%d %H:%M:%S %Z}D\036" synopsis last-modified')

    def test_08_build_format_unknown(self):
        """ build_format with unknown field """
        self.assertEqual(self.db.build_format(['synopsis', 'enum-fld', 'fred']),
            '"%s\037%s\037%s\036" synopsis enum-fld fred')

    def test_09_build_format_table_field(self):
        """ build_format with bare table field colnames"""
        self.assertEqual(self.db.build_format(['username', 'datetime'],
                                              table_field='change-log'),
            '"%s\034%{%Y-%m-%d %H:%M:%S %Z}D\035" username datetime')

    def test_09a_build_format_table_columns(self):
        """ build_format with qualified table field colnames """
        self.assertEqual(
            self.db.build_format(['change-log.username', 'change-log.datetime'],
                                 table_field='change-log'),
            '"%s\034%{%Y-%m-%d %H:%M:%S %Z}D\035" '
            'change-log.username change-log.datetime')

    def test_10_unparse_pr_no_from(self):
        """ unparse_pr raises if from: header missing """
        #text = {'state':'open', 'synopsis':'This is a test',}
        #expected = ">Synopsis: This is a test\n>State: open"
        #self.assertEquals(self.conn.unparse_pr(text), expected)
        pr = {"foo":"bar"}
        self.assertRaises(gnats.GnatsException, self.db.unparse_pr, pr)

    def test_11_unparse_pr_no_number(self):
        """ unparse_pr without Number field """
        # Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified
        pr = {'enum-fld':'gnats', 'synopsis':'This is a test', 'multienum-fld':'',
              'multitext-fld':'some long\ntext.', 'last-modified':'2008-01-01',
              'identifier':[('1', {'scoped-enum-fld':'open'}),], 'from:':'me',}
        expected = """From: me

>Synopsis:       This is a test
>Enum-fld:       gnats
>MultiEnum-fld:  \n>Multitext-fld:
some long
text.
>Scoped-Enum-fld{1}: open"""
        self.assertEquals(self.db.unparse_pr(pr), expected)

    def test_12_unparse_pr_number(self):
        """ unparse_pr with Number field """
        # Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified
        pr = {'number':'100', 'enum-fld':'gnats', 'synopsis':'This is a test',
              'multitext-fld':'some long\ntext.', 'last-modified':'2008-01-01',
              'identifier':[('1', {'scoped-enum-fld':'open'}),], 'from:':'me',}
        expected = """From: me

>Number:         100
>Synopsis:       This is a test
>Enum-fld:       gnats
>Multitext-fld:
some long
text.
>Scoped-Enum-fld{1}: open"""
        self.assertEquals(self.db.unparse_pr(pr), expected)

    def test_13_unparse_pr_empty_multi(self):
        """ unparse_pr with empty multitext field """
        # Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified
        pr = {'number':'100', 'enum-fld':'gnats', 'synopsis':'This is a test',
              'last-modified':'2008-01-01', 'multitext-fld':'',
              'identifier':[('1', {'scoped-enum-fld':'open'}),], 'from:':'me',}
        expected = """From: me

>Number:         100
>Synopsis:       This is a test
>Enum-fld:       gnats
>Multitext-fld:
>Scoped-Enum-fld{1}: open"""
        self.assertEquals(self.db.unparse_pr(pr), expected)

    def test_14_unparse_pr_change_reason(self):
        """ unparse_pr with change-reason """
        # Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified
        pr = {'number':'100', 'enum-fld':'gnats', 'enum-fld-changed-why':'boo',
              'synopsis':'This is a test', 'last-modified':'2008-01-01',
              'identifier':[('1', {'scoped-enum-fld':'open'}),], 'from:':'me',}
        expected = """From: me

>Number:         100
>Synopsis:       This is a test
>Enum-fld:       gnats
>Enum-fld-Changed-Why:
boo
>Scoped-Enum-fld{1}: open"""
        self.assertEquals(self.db.unparse_pr(pr), expected)

    def test_15_unparse_pr_scoped_change_reason(self):
        """ unparse_pr with scoped change-reason """
        # Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified
        pr = {'number':'100', 'enum-fld':'gnats', 'multienum-fld':'',
              'synopsis':'This is a test', 'last-modified':'2008-01-01',
              'identifier':[('1', {'scoped-enum-fld':'open',
                   'scoped-enum-fld-changed-why':'boo',}),], 'from:':'me',}
        expected = """From: me

>Number:         100
>Synopsis:       This is a test
>Enum-fld:       gnats
>MultiEnum-fld:  \n>Scoped-Enum-fld{1}: open
>Scoped-Enum-fld-Changed-Why{1}:
boo"""
        self.assertEquals(self.db.unparse_pr(pr), expected)

    def test_16_unparse_pr_bogus_scope(self):
        """ unparse_pr with bogus scope """
        # Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified
        pr = {'number':'100', 'enum-fld':'gnats', 'multienum-fld':'foo:bar',
              'synopsis':'This is a test', 'last-modified':'2008-01-01',
              'identifier':[('', {'scoped-enum-fld':'open',}),], 'from:':'me',}
        expected = """From: me

>Number:         100
>Synopsis:       This is a test
>Enum-fld:       gnats
>MultiEnum-fld:  foo:bar"""
        self.assertEquals(self.db.unparse_pr(pr), expected)

    def test_17_unparse_pr_fake_read_only(self):
        """ unparse_pr with fake read-only field """
        # Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified
        pr = {'number':'100', 'enum-fld':'gnats', 'synopsis':'This is a test',
              'multitext-fld':'some long\ntext.', 'last-modified':'2008-01-01',
              'identifier':[('1', {'scoped-enum-fld':'open'}),], 'from:':'me',}
        expected = """From: me

>Number:         100
>Synopsis:       This is a test
>Enum-fld:       gnats
>Multitext-fld:
some long
text.
>Scoped-Enum-fld{1}: open"""
        self.db.fields['synopsis'].read_only = True
        self.assertEquals(self.db.unparse_pr(pr), expected)

    def test_18_unparse_pr_table_field(self):
        """ unparse_pr skips table field even if not read_only """
        # Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified

        pr = {'number':'100', 'enum-fld':'gnats', 'synopsis':'This is a test',
              'multitext-fld':'some long\ntext.', 'last-modified':'2008-01-01',
              'identifier':[('1', {'scoped-enum-fld':'open'}),], 'from:':'me',
              'change-log':'foo',}
        expected = """From: me

>Number:         100
>Synopsis:       This is a test
>Enum-fld:       gnats
>Multitext-fld:
some long
text.
>Scoped-Enum-fld{1}: open"""
        self.db.fields['change-log'].read_only = False
        self.assertEquals(self.db.unparse_pr(pr), expected)

    def test_19_unparse_pr_multienum_as_list(self):
        """ unparse_pr handles multienums given as lists """
        pr = {'number':'100', 'enum-fld':'gnats', 'synopsis':'This is a test',
              'multienum-fld':['foo', 'bar'], 'last-modified':'2008-01-01',
              'identifier':[('1', {'scoped-enum-fld':'open'}),], 'from:':'me',
              'change-log':'foo',}
        expected = """From: me

>Number:         100
>Synopsis:       This is a test
>Enum-fld:       gnats
>MultiEnum-fld:  foo:bar
>Scoped-Enum-fld{1}: open"""
        self.assertEquals(self.db.unparse_pr(pr), expected)

    def test_20_unparse_pr_trailing_whitespace_multi(self):
        """ unparse_pr, multitext field with trailing whitespace """
        # Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified
        pr = {'number':'100', 'enum-fld':'gnats', 'synopsis':'This is a test',
              'last-modified':'2008-01-01', 'multitext-fld':'a\ntest\n\n',
              'identifier':[('1', {'scoped-enum-fld':'open'}),], 'from:':'me',}
        expected = """From: me

>Number:         100
>Synopsis:       This is a test
>Enum-fld:       gnats
>Multitext-fld:
a
test

>Scoped-Enum-fld{1}: open"""
        self.assertEquals(self.db.unparse_pr(pr), expected)

    def test_21_builtin(self):
        """ Check that builtin() works for last-modified """
        self.assertEqual(self.db.builtin('last-modified'), 'last-modified')

    def test_22_builtin_non_existent(self):
        """ Check that builtin() returns empty string for non-existent field """
        self.assertEqual(self.db.builtin('fred'), '')

    def test_23_add_space_beggining_multiline(self):
        """ unparse_pr, add a space in the beginning of multitext field, if it
        contains data in the format '>fld: fld-value'. """
        # Number Synopsis Enum-fld Scoped-Enum-fld MultiEnum-fld Multitext-fld Last-Modified
        pr = {'number':'100', 'enum-fld':'gnats', 'synopsis':'This is a test',
              'last-modified':'2008-01-01',
              'multitext-fld':'some text\n>from: fld-value\n>fld: fld-value',
              'identifier':[('1', {'scoped-enum-fld':'open'}),], 'from:':'me',}
        expected = """From: me

>Number:         100
>Synopsis:       This is a test
>Enum-fld:       gnats
>Multitext-fld:
some text
 >from: fld-value
 >fld: fld-value
>Scoped-Enum-fld{1}: open"""
        self.assertEquals(self.db.unparse_pr(pr), expected)

class T05_ValidateField(unittest.TestCase):
    """ validate_field() """

    def setUp(self):
        unittest.TestCase.setUp(self)
        server = gnats.Server('somehost')
        conn = FakeServerConnectionForDB(server)
        self.db = Database(server, 'testdb', conn)

    def test_01_field_raises_on_invalid(self):
        """ validate_field raises on invalid field """
        self.assertRaises(gnats.InvalidFieldNameException,
                          self.db.validate_field, 'not-valid', {})

    def test_02_field_required_absent(self):
        """ validate_field complains on absent required value """
        out = self.db.validate_field('synopsis', {})
        self.assertTrue(len(out) == 1)
        self.assertTrue(out[0].lower().find('required') > -1)

    def test_03_field_required_blank(self):
        """ validate_field complains on blank required value """
        out = self.db.validate_field('synopsis', {'synopsis': ''})
        self.assertTrue(len(out) == 1)
        self.assertTrue(out[0].lower().find('required') > -1)

    def test_04_field_required_present(self):
        """ validate_field finds required value """
        out = self.db.validate_field('synopsis', {'synopsis': 'foo'})
        self.assertTrue(len(out) == 0)

    def test_05_field_enum_invalid(self):
        """ validate_field complains about invalid enum """
        out = self.db.validate_field('enum-fld', {'enum-fld': 'foo',})
        self.assertTrue(len(out) == 1)
        self.assertTrue(out[0].lower().find('illegal') > -1)

    def test_06_field_enum_valid(self):
        """ validate_field accepts valid enum """
        out = self.db.validate_field('enum-fld', {'enum-fld': 'cat1',})
        self.assertTrue(len(out) == 0)

    def test_07_field_enum_allow_any(self):
        """ validate_field honors allow_any_value """
        self.db.fields['enum-fld'].allow_any_value = True
        out = self.db.validate_field('enum-fld', {'enum-fld': 'foo',})
        self.assertTrue(len(out) == 0)

    def test_08_field_change_reason_missing(self):
        """ validate_field complains about missing change-reason """
        out = self.db.validate_field('enum-fld', {'enum-fld': 'cat2',},
                                     check_cr=True)
        self.assertTrue(len(out) == 1)
        self.assertTrue(out[0].lower().find('change reason') > -1)

    def test_09_field_change_reason_present(self):
        """ validate_field finds supplied change-reason """
        out = self.db.validate_field('enum-fld', {'enum-fld': 'cat2',
            'enum-fld-changed-why': 'foo',}, check_cr=True)
        self.assertTrue(len(out) == 0)

    def test_10_field_multienum_string(self):
        """ Valid multienum value supplied as string """
        out = self.db.validate_field('multienum-fld',
                                     {'multienum-fld': 'product1:product2',})
        self.assertTrue(len(out) == 0)

    def test_11_field_bad_multienum_string(self):
        """ Invalid multienum value supplied as string """
        out = self.db.validate_field('multienum-fld',
                                     {'multienum-fld': 'productX:product2',})
        self.assertTrue(out[0].find('productX') > -1)

    def test_12_field_multienum_list(self):
        """ Valid multienum value supplied as list """
        out = self.db.validate_field('multienum-fld',
            {'multienum-fld': 'product1 product2'.split(),})
        self.assertTrue(len(out) == 0)

    def test_13_field_bad_multienum_list(self):
        """ Invalid multienum value supplied as list """
        out = self.db.validate_field('multienum-fld',
            {'multienum-fld': 'product1 productY'.split(),})
        self.assertTrue(out[0].find('productY') > -1)

    def test_14_field__multienum_bad_input_type(self):
        """ Multienum value supplied as non-list, non-string """
        out = self.db.validate_field('multienum-fld',
            {'multienum-fld': 1234,})
        self.assertTrue(out[0].find('neither') > -1)


class T06_Validate(unittest.TestCase):
    """ _validate """

    def setUp(self):
        unittest.TestCase.setUp(self)
        server = gnats.Server('somehost')
        conn = FakeServerConnectionForDB(server)
        self.db = Database(server, 'testdb', conn)
        self.db.validate_field = self.my_validate_field
        self.fname_in = []
        self.pr_in = []
        self.check_cr_in = []
        self.vf_out = []

    def my_validate_field(self, fname, pr, check_cr=False):
        self.fname_in.append(fname)
        self.pr_in.append(pr)
        self.check_cr_in.append(check_cr)
        return self.vf_out.pop()

    def test_01_initial(self):
        """ initial entry fields """
        test_pr = {'synopsis': 'foo',
                   'identifier': [(1, {'scoped-enum-fld': 'foo'}),],
                   }
        self.vf_out = [[], [], [], []]
        out = self.db._validate(test_pr, 'initial')
        self.assertEqual(self.fname_in,
                         'synopsis enum-fld multitext-fld from:'.split())
        self.assertEqual(out, {})

    def test_02_initial_errors(self):
        """ initial entry fields with errors """
        test_pr = {'synopsis': 'foo',
                   'identifier': [(1, {'scoped-enum-fld': 'foo'}),],
                   }
        self.vf_out = [[], [1], [], [2]]
        out = self.db._validate(test_pr, 'initial')
        self.assertEqual(self.fname_in,
                         'synopsis enum-fld multitext-fld from:'.split())
        self.assertEqual(out,
                         {'synopsis': [2], 'multitext-fld': [1],})

    def test_03_non_scoped(self):
        """ non-scoped fields """
        test_pr = {'synopsis': 'foo', 'enum-fld': 'bar',}
        self.vf_out = [[], []]
        out = self.db._validate(test_pr, 'fields')
        self.assertEqual(self.fname_in,
                         'synopsis enum-fld'.split())
        self.assertEqual(out, {})

    def test_04_non_scoped_errors(self):
        """ non-scoped fields with errors """
        test_pr = {'synopsis': 'foo', 'enum-fld': 'bar',}
        self.vf_out = [[1], []]
        out = self.db._validate(test_pr, 'fields')
        self.assertEqual(self.fname_in,
                         'synopsis enum-fld'.split())
        self.assertEqual(out,
                         {'enum-fld': [1],})

    def test_05_scoped(self):
        """ scoped fields only """
        test_pr = {'identifier': [(1, {'scoped-enum-fld': 'foo'}),],}
        self.vf_out = [[], []]
        out = self.db._validate(test_pr, 'fields')
        self.assertEqual(self.fname_in,
                         'scoped-enum-fld'.split())
        self.assertEqual(out, {})

    def test_06_scoped_error(self):
        """ scoped fields only, with error """
        test_pr = {'identifier': [(1, {'scoped-enum-fld': 'foo'}),],}
        self.vf_out = [[1]]
        out = self.db._validate(test_pr, 'fields')
        self.assertEqual(self.fname_in,
                         ['scoped-enum-fld'])
        self.assertEqual(out,
                         {'scoped-enum-fld{1}': [1],})

    def test_07_non_scoped_change_reason(self):
        """ non-scoped fields with change-reason """
        test_pr = {'synopsis': 'foo', 'enum-fld': 'bar',}
        self.vf_out = [[], []]
        out = self.db._validate(test_pr, 'fields-cr')
        self.assertEqual(self.fname_in,
                         'synopsis enum-fld'.split())
        self.assertEqual(out, {})
        self.assertEqual(self.check_cr_in, [True, True])

    def test_08_scoped_change_reason(self):
        """ scoped fields only, with change-reason"""
        test_pr = {'identifier': [(1, {'scoped-enum-fld': 'foo'}),],}
        self.vf_out = [[], []]
        out = self.db._validate(test_pr, 'fields-cr')
        self.assertEqual(self.fname_in,
                         'scoped-enum-fld'.split())
        self.assertEqual(out, {})
        self.assertEqual(self.check_cr_in, [True])

    def test_09_scoped_and_non(self):
        """ Scoped and non-scoped fields """
        test_pr = {'synopsis': 'foo',
                   'identifier': [(1, {'scoped-enum-fld': 'foo'}),],
                   }
        self.vf_out = [[], []]
        out = self.db._validate(test_pr, 'fields')
        self.assertEqual(self.fname_in,
                         'synopsis scoped-enum-fld'.split())
        self.assertEqual(out, {})

    def test_10_scoped_and_non_error_scoped(self):
        """ Scoped and non-scoped fields, with scoped error """
        test_pr = {'synopsis': 'foo',
                   'identifier': [(1, {'scoped-enum-fld': 'foo'}),],
                   }
        self.vf_out = [[1], []]
        out = self.db._validate(test_pr, 'fields')
        self.assertEqual(self.fname_in,
                         'synopsis scoped-enum-fld'.split())
        self.assertEqual(out,
                         {'scoped-enum-fld{1}': [1],})

    def test_11_scoped_and_non_error_non(self):
        """ Scoped and non-scoped fields, with non-scoped error """
        test_pr = {'synopsis': 'foo',
                   'identifier': [(1, {'scoped-enum-fld': 'foo'}),],
                   }
        self.vf_out = [[], [1]]
        out = self.db._validate(test_pr, 'fields')
        self.assertEqual(self.fname_in,
                         'synopsis scoped-enum-fld'.split())
        self.assertEqual(out,
                         {'synopsis': [1],})

    def test_12_skips_read_only(self):
        """ skips read-only fields """
        test_pr = {'synopsis': 'foo', 'last-modified': 'bar',}
        self.vf_out = [[]]
        out = self.db._validate(test_pr, 'fields')
        self.assertEqual(self.fname_in,
                         ['synopsis'])
        self.assertEqual(out, {})

    def test_13_all_fields(self):
        """ all fields """
        test_pr = {'synopsis': 'foo', 'last-modified': 'bar',
                   'identifier': [(1, {'scoped-enum-fld': 'foo'}),],}
        self.vf_out = [[], [], [], [], [],]
        out = self.db._validate(test_pr, 'all')
        self.assertEqual(self.fname_in,
            'synopsis enum-fld multienum-fld multitext-fld scoped-enum-fld'.split())
        self.assertEqual(out, {})

    def test_14_all_fields_errors(self):
        """ all fields, with errors """
        test_pr = {'synopsis': 'foo', 'last-modified': 'bar',
                   'identifier': [(1, {'scoped-enum-fld': 'foo'}),],}
        self.vf_out = [[1], [2], [], [], [],]
        out = self.db._validate(test_pr, 'all')
        self.assertEqual(self.fname_in,
            'synopsis enum-fld multienum-fld multitext-fld scoped-enum-fld'.split())
        self.assertEqual(out, {'multitext-fld': [2],
                               'scoped-enum-fld{1}': [1],})


class T07_ValidatePR(unittest.TestCase):
    """ PR validation methods """

    def setUp(self):
        unittest.TestCase.setUp(self)
        server = gnats.Server('somehost')
        conn = FakeServerConnectionForDB(server)
        self.db = Database(server, 'testdb', conn)
        self.db._validate = self.my_validate
        self.pr_in = ''
        self.validate_in = ''

    def my_validate(self, pr, validate):
        self.pr_in = pr
        self.validate_in = validate
        return 1

    def test_01_validate_fields(self):
        """ validate_fields() """
        self.db.validate_fields('pr', change_reasons=False)
        self.assertEqual(self.pr_in, 'pr')
        self.assertEqual(self.validate_in, 'fields')

    def test_02_validate_fields_cr(self):
        """ validate_fields() with change-reasons """
        self.db.validate_fields('pr', change_reasons=True)
        self.assertEqual(self.pr_in, 'pr')
        self.assertEqual(self.validate_in, 'fields-cr')

    def test_03_validate_pr(self):
        """ validate_pr() """
        self.db.validate_pr('pr')
        self.assertEqual(self.pr_in, 'pr')
        self.assertEqual(self.validate_in, 'all')

    def test_04_validate_initial(self):
        """ validate_initial() """
        self.db.validate_initial('pr')
        self.assertEqual(self.pr_in, 'pr')
        self.assertEqual(self.validate_in, 'initial')


class T08_MetadataLevels(unittest.TestCase):
    """ Test Database class metadata with different package-level metadata
    settings. """

    def setUp(self):
        self.server = gnats.Server('somehost')
        self.conn = FakeServerConnectionForDB(self.server)
        gnats.metadata_level = gnats.FULL_METADATA

    def tearDown(self):
        gnats.metadata_level = gnats.FULL_METADATA

    def test_01_full(self):
        """ FULL_METADATA """
        gnats.metadata_level = gnats.FULL_METADATA
        db = Database(self.server, 'testdb', self.conn)
        self.assertEqual(db.name, 'testdb')
        self.assertEqual(db.description, 'Fake Database')
        self.assertEqual(len(db.list_fields()), 8)
        self.assertEqual(len(db.initial_entry_fields), 4)
        self.assertEqual(db.fields['synopsis'].lcname, 'synopsis')
        self.assertEqual(db.fields['synopsis'].name, 'Synopsis')
        self.assertEqual(db.fields['synopsis'].description,
                         'Synopsis field')
        self.assertEqual(db.fields['enum-fld'].values[0], 'cat1')

    def test_02_no_enum(self):
        """ NO_ENUM_METADATA """
        gnats.metadata_level = gnats.NO_ENUM_METADATA
        db = Database(self.server, 'testdb', self.conn)
        self.assertEqual(db.name, 'testdb')
        self.assertEqual(db.description, 'Fake Database')
        self.assertEqual(len(db.list_fields()), 8)
        self.assertEqual(db.builtin('number'), 'number')
        self.assertRaises(GnatsException, db._validate, 1, 1)
        self.assertRaises(GnatsException, db.validate_field, 1, 1)
        self.assertEqual(len(db.initial_entry_fields), 4)
        self.assertEqual(db.fields['synopsis'].lcname, 'synopsis')
        self.assertEqual(db.fields['synopsis'].name, 'Synopsis')
        self.assertEqual(db.fields['synopsis'].description,
                         'Synopsis field')
        self.assertEqual(len(db.fields['enum-fld'].values), 0)
        self.assertRaises(GnatsException, db.fields['enum-fld'].list_values)

    def test_03_minimal(self):
        """ MINIMAL_METADATA """
        gnats.metadata_level = gnats.MINIMAL_METADATA
        db = Database(self.server, 'testdb', self.conn)
        self.assertEqual(db.name, 'testdb')
        self.assertEqual(db.description, '')
        self.assertEqual(db.builtin('number'), 'number')
        self.assertEqual(len(db.list_fields()), 8)
        self.assertEqual(len(db.initial_entry_fields), 0)
        self.assertEqual(db.fields['synopsis'].lcname, 'synopsis')
        self.assertEqual(db.fields['synopsis'].description, '')
        self.assertEqual(len(db.fields['enum-fld'].values), 0)

    def test_03_none(self):
        """ NO_METADATA """
        gnats.metadata_level = gnats.NO_METADATA
        db = Database(self.server, 'testdb', self.conn)
        self.assertEqual(db.name, 'testdb')
        self.assertEqual(db.description, '')
        self.assertRaises(GnatsException, db.unparse_pr, 1)
        self.assertRaises(GnatsException, db.build_format, 1)
        self.assertRaises(GnatsException, db.builtin, 1)
        self.assertRaises(GnatsException, db.list_fields)
        self.assertEqual(len(db.initial_entry_fields), 0)
        self.assertEqual(len(db.fields), 0)

    def test_04_refresh_true(self):
        """ refresh_metadata_automatically honored if True """
        gnats.refresh_metadata_automatically = True
        db = Database(self.server, 'testdb', self.conn)
        def cb(dbx):
            cb.dbin = dbx
        cb.dbin = None
        db.post_metadata_callback = cb
        # "Refresh" the conn, so that metadata can run again
        self.conn = FakeServerConnectionForDB(self.server)
        db.last_config_time = 987
        db.get_handle('user', 'pass', self.conn)
        self.assertEqual(cb.dbin, db)

    def test_05_refresh_false(self):
        """ refresh_metadata_automatically honored if False"""
        gnats.refresh_metadata_automatically = False
        db = Database(self.server, 'testdb', self.conn)
        def cb(dbx):
            cb.dbin = dbx
        cb.dbin = None
        db.post_metadata_callback = cb
        # "Refresh" the conn, so that metadata can run again
        self.conn = FakeServerConnectionForDB(self.server)
        db.last_config_time = 987
        db.get_handle('user', 'pass', self.conn)
        self.assertEqual(cb.dbin, None)


classes = (
          T01_DatabaseMetadata,
          T02_FieldMetadata,
          T03_EnumField,
          T03a_TableField,
          T04_DatabaseMethods,
          T05_ValidateField,
          T06_Validate,
          T07_ValidatePR,
          T08_MetadataLevels,
          )

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    suites = []
    for cl in classes:
        suites.append(unittest.makeSuite(cl, 'test'))
    runner.run(unittest.TestSuite(suites))
