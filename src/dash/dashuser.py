'''
Created on Jul 19, 2013

@author: richilb
'''

import os
import re

class Dashuser(object):
    
    
    # Get the list of all dashboard users from ldap and store it in dashuserlist 
    def __init__(self):
        self.dashuserlist = []
        for line in os.popen("ldapsearch -x -b 'dc=juniper, dc=net' -h authldap.juniper.net 'authGroupName=dashboard-users' | grep uid"):
            r = re.compile('uid=(.*?),')
            m = r.search(line)
            if m:
                self.dashuserlist.append(m.group(1))

