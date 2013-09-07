'''
Created on Jun 12, 2013

@author: richilb
'''

import json, sys
from verify import Verify


if len(sys.argv) > 1:
    RUNPATH = sys.argv[1]
else:
    RUNPATH = '../bin'
    
LOGPATH = RUNPATH + '/logs'
CONFIGFILE = RUNPATH + '/DAM.config'

config_data= open(CONFIGFILE).read()
data = json.loads(config_data)

USERLIST = [json.dumps(u).strip('"') for u in data["userlist"]] 
RULELIST = [json.dumps(r).strip('"') for r in data["rulelist"]]
SERVER = json.dumps(data["server"]).strip('"')

print 'Runpath: ', RUNPATH
print 'Logpath: ', LOGPATH
print 'Server from config file: ', SERVER
print 'Userlist from config file: ', USERLIST
print 'Rulelist from config file: ', RULELIST
 

v = Verify(LOGPATH, SERVER)
v.run(USERLIST, RULELIST)
