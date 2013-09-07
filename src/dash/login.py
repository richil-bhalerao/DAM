'''
Created on Jun 12, 2013

@author: richilb
'''

import urllib2
import getpass
import pwd
import sys

class Login(object):
    
    def __init__(self):
        self.__username = 'dashboard'
        self.__password = 'dashboard'
 
    
    # Access the dashboard web page by specifying login credentials and other details    
    def getPage(self, url = None):
        if url == None:
            url = 'https://deepthought.juniper.net/dashboard/agenda/junos'
            
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.__username, self.__password)
        
        # create the AuthHandler
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)
        
        # ...and install it globally so it can be used with urlopen.
        page = None
        try:
            page = urllib2.urlopen(url).read()
        except urllib2.HTTPError:
            print "** Error in connecting to dashboard: connection timeout... "
            sys.exit() 
        
        return page

