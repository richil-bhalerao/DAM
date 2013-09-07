"""
GNATS protocol codes.

Dirk Bergstrom, dirk@juniper.net, 2008-04-17

Copyright (c) 2008-2009, Juniper Networks, Inc.
All rights reserved.
"""

# The standard GNATS port
DEFAULT_PORT = 1529

# The database credentials
DEFAULT_USER = 'prdb_junos'
DEFAULT_PASSWORD = 'prdb_junos'
DEFAULT_DB = 'pswtools'

# Audit-Trail Query and Fields
AT_QUERY = "SELECT AUDIT_TRAIL_ROW_ID, AUDIT_TRAIL_USERNAME, \
                to_char(AUDIT_TRAIL_DATETIME, 'YYYY-MM-DD HH24:MI:SS TZHTZM'), \
                AUDIT_TRAIL_INFO FROM AUDIT_TRAIL WHERE ID=%s \
                ORDER BY AUDIT_TRAIL_ROW_ID"
AT_FIELDS = ['row-id', 'username', 'datetime', 'info' ]

# Change-Log Query and Fields
CL_QUERY = "SELECT CHANGE_LOG_ROW_ID, CHANGE_LOG_USERNAME, \
                to_char(CHANGE_LOG_DATETIME, 'YYYY-MM-DD HH24:MI:SS TZHTZM'), \
                CHANGE_LOG_FIELD, CHANGE_LOG_FROM, CHANGE_LOG_TO, \
                CHANGE_LOG_REASON, CHANGE_LOG_SCOPE FROM CHANGE_LOG WHERE \
                ID=%s ORDER BY CHANGE_LOG_ROW_ID"
CL_FIELDS = ['row-id', 'username', 'datetime', 'field', 
                'from', 'to', 'reason', 'scope']

# Separators for building query formats
COL_SEP = '\034'
ROW_SEP = '\035'
RECORD_SEP = '\036'
FIELD_SEP = '\037#\037'

# Field flags
FLAG_REQUIRE_CHANGE_REASON = 'requireChangeReason'
FLAG_REQUIRED = 'required'
FLAG_READ_ONLY = 'readonly'
FLAG_MULTI_VALUED = 'multivalued'
FLAG_TEXT_SEARCH = 'textsearch'
FLAG_REQ_COND = 'req-cond'
FLAG_ALLOW_ANY_VALUE = 'allowAnyValue'

# The possible values of a server reply type.  REPLY_CONT means that there
# are more reply lines that will follow; REPLY_END Is the final line.
REPLY_CONT = 1
REPLY_END = 2


# we use the access levels defined in gnatsd.h to do
# access level comparisons
#define ACCESS_UNKNOWN  0x00
#define ACCESS_DENY     0x01
#define ACCESS_NONE     0x02
#define ACCESS_SUBMIT   0x03
#define ACCESS_VIEW     0x04
#define ACCESS_VIEWCONF 0x05
#define ACCESS_EDIT     0x06
#define ACCESS_ADMIN    0x07
LEVEL_TO_CODE = {'deny': 1, 'none': 2, 'submit' : 3, 'view' : 4,
                 'viewconf' : 5, 'edit' : 6, 'admin': 7}

# Variations on OK
CODE_GREETING = '200'
CODE_CLOSING = '201'
CODE_OK = '210'
CODE_SEND_PR = '211'
CODE_SEND_TEXT = '212'
CODE_SEND_CHANGE_REASON = '213'
CODE_NO_PRS_MATCHED = '220'
CODE_NO_ADM_ENTRY = '221'

# Continuation codes
CODE_PR_READY = '300'
CODE_TEXT_READY = '301'
CODE_INFORMATION = '350'
CODE_INFORMATION_FILLER = '351'

# Errors
CODE_NONEXISTENT_PR = '400'
CODE_EOF_PR = '401'
CODE_UNREADABLE_PR = '402'
CODE_INVALID_PR_CONTENTS = '403'
CODE_MISSING_CHANGE_REASON = '405'
CODE_INVALID_FIELD_NAME = '410'
CODE_INVALID_ENUM = '411'
CODE_INVALID_DATE = '412'
CODE_INVALID_FIELD_CONTENTS = '413'
CODE_INVALID_SEARCH_TYPE = '414'
CODE_INVALID_EXPR = '415'
CODE_INVALID_LIST = '416'
CODE_INVALID_DATABASE = '417'
CODE_INVALID_QUERY_FORMAT = '418'
CODE_INVALID_FIELD_EDIT = '419'
CODE_NO_KERBEROS = '420'
CODE_AUTH_TYPE_UNSUP = '421'
CODE_NO_ACCESS = '422'
CODE_LOCKED_PR = '430'
CODE_GNATS_LOCKED = '431'
CODE_GNATS_NOT_LOCKED = '432'
CODE_PR_NOT_LOCKED = '433'
CODE_READONLY_FIELD = '434'
CODE_INVALID_FTYPE_PROPERTY = '435'
CODE_CMD_ERROR = '440'
CODE_WRITE_PR_FAILED = '450'

# Serious errors
CODE_ERROR = '600'
CODE_TIMEOUT = '610'
CODE_NO_GLOBAL_CONFIG = '620'
CODE_INVALID_GLOBAL_CONFIG = '621'
CODE_INVALID_INDEX = '622'
CODE_NO_INDEX = '630'
CODE_FILE_ERROR = '640'
