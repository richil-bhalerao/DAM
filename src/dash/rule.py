'''
Created on Jun 12, 2013

@author: richilb
'''


import os, gnats, getpass, copy, datetime
from hier import Hier
from category import Category
from dashuser import Dashuser

class Rule(object):
    
    # Initialize the connection string required to connect to GNATS database
    def __init__(self):
        self.hier = Hier()
        self.category = Category()
        self.dashuser = Dashuser()
        
        host = 'gnats.juniper.net'
        db = 'default'
        
        # username = os.getusername()  ... for Linux
        
        username = getpass.getuser()        #... for Windows and linux
        
        # Get a database object, which holds the metadata (field names, etc.)
        self.db_obj = gnats.get_database(host, db)
        # Get a db handle, a connection to the server
        self.db_handle = self.db_obj.get_handle(username, passwd='*')

    
    # build an OR query e.g.: (responsible == "user1" | responsible == "user2"...)
    def getORquery(self, field, userlist, op = '=='):
        
        query = ''
        concat = ''
        for user in userlist:
            query += concat
            query += ''.join('(%(1)s %(2)s "%(3)s")' % {"1": field, "2": op, "3": user})
            concat = ' | '
            
        return '(%s)' % query
    
    # Using employee hierarchy build a list of all reports of a particular manager
    def buildUserList(self, responsible):
        userlist = self.hier.reports(responsible, 0)
        # we should also consider count of that user if he/she is a manager 
        userlist.append(responsible)
        return userlist
    
    # Filter out user list to remove users which are not under JUNOS system
    def buildJunosUserList(self, responsible):
        userlist = self.hier.reports(responsible, 0)
        # we should also consider count of that user if he/she is a manager 
        userlist.append(responsible)
        # remove those users which are not junos dashboard users
        userlistcopy = copy.copy(userlist)
        for user in userlistcopy:
            if user not in self.dashuser.dashuserlist:
                userlist.remove(user)
        
        return userlist
        
        
    '''
    Build list of all reports for category or category alias:
    if islias = 1 -> generate alias list
    if isalias = 0 -> generate catgeory list
    '''
    def buildCatAliasList(self, responsible, isAlias=1):
        aliaslist = []
        userlist = self.buildUserList(responsible)
        for user in userlist:
            if isAlias == 1:
                alist = self.category.listAliasForUser(user)
            else:
                alist = self.category.listCategoriesForUser(user) 
            if alist != None:
                for a in alist:
                    aliaslist.append(a)
        
        # remove duplicates
        aliaslist = list(set(aliaslist))
        return aliaslist
    
    '''
    Build query as:
    responsible == Aliaslist & (dev-owner == "" | dev-owner == Aliaslist) & Category == Categorylist
    '''
    def getCategoryOwnerQuery(self, responsible):
        aliaslist = self.buildCatAliasList(responsible)
        catlist = self.buildCatAliasList(responsible, 0)
        
        if len(aliaslist) > 0:
            return '| (%(1)s & (dev-owner == "" | %(2)s) & %(3)s)' % {"1": self.getORquery('responsible', aliaslist), \
                                                                      "2": self.getORquery('dev-owner', aliaslist, '~'), \
                                                                      "3": self.getORquery('category', catlist)}
        else:
            return ''
            
    
    # generate rule specific query e.g.: blocker == "test"
    def getQueryForRuleType(self, ruletype):
        if ruletype.lower() == 'test blocker':
            return '(blocker == "test")'
        elif ruletype.lower() == "regression":
            return '(attributes ~ "regression-pr")'
        elif ruletype.lower() == "beta blocker":
            return '((blocker == "beta") | ((planned-release ~ "b1" | planned-release ~ "b2" | planned-release ~ "b3") & (blocker != "")))'
        elif ruletype.lower() == "cl1":
            return '(problem-level == "1-CL1")'
        elif ruletype.lower() == "cl2":
            return '(problem-level == "2-CL2")'
        elif ruletype.lower() == "il1":
            return '(problem-level == "3-IL1")'
        elif ruletype.lower() == "il2":
            return '(problem-level == "4-IL2")'
    
    # Get the count if PRs from the PRlist that was generated                
    def getCount(self, responsible, ruletype):
        try:
            # Run the query
            PRlist = self.getPRlist(responsible, ruletype)
            return len(PRlist)
        except gnats.GnatsException, err:
            print "Error in query: %s" % err.message
            return 0
    
    '''
    Connect to the GNATS database using GNATS python API and fire the query-exp built to get the PR list
    => psuedo query logic for getting test blocker type PRs:
    (
      (responsible = junosUserlist or (dev-owner = junosUserlist & state != feedback) ) or
     (responsible = categoryAliasList & (dev-owner = "" or dev-owner ~ categoryAliasList) & Category == CategoryList) or
    )
    & blocker == "test"
    & (state != "closed" & state != "suspended" & state != "monitored") 
    & product[group] == "junos"
    '''
    def getPRlist(self, responsible, ruletype):
        # The columns we want, and the query
        columns = ['number', 'last-modified']

        # Build the junosuserlist which are users who fall under junos dashboard
        junosuserlist = self.buildJunosUserList(responsible)
        # print 'Junos user list', junosuserlist        
        expr = ''' (   %(1)s | 
                       (%(2)s & state != "feedback") 
                       %(3)s
                    ) 
                    & %(4)s 
                    & (state != "closed" & state != "suspended" & state != "monitored")  
                    & product[group] == "junos" ''' \
        % {"1": self.getORquery('responsible', junosuserlist), "2": self.getORquery('dev-owner', junosuserlist), \
           "3": self.getCategoryOwnerQuery(responsible), "4": self.getQueryForRuleType(ruletype)}
        
        
        #print 'Expression used: %s ' % expr
        
        try:
            # Run the query
            prs = self.db_handle.query(expr, columns, sort=(('number', 'desc'),))
            PRlist = []
            for prno in prs:
                PRlist.append(str(prno[0]))
            return PRlist
        except gnats.GnatsException, err:
            print "Error in query: %s" % err.message
            return 0

    '''
    Get PR number, last modified datetime, responsible and category values for the PRs in the list provided.
    This information is used to discard those PRs which are not supposed to be there in the discrepancy list.
    '''   
    def getPRdict(self, PRlist):
        # The columns we want, and the query
        columns = ['number', 'last-modified', 'responsible', 'category']
        expr = '%s' % self.getORquery('number', [PR for PR in PRlist])
        try:
            # Run the query
            prs = self.db_handle.query(expr, columns, sort=(('number', 'desc'),))
            PRdict = {}
            for prno in prs:
                # if responsible is not in junos system discard the discrepancy
                if (prno[2] not in self.dashuser.dashuserlist) or (prno[2] not in self.category.listAllCategories()):
                    #print 'user removed: ', prno[2]
                    continue
                
                # if category is not in junos system discard the discrepancy
                if prno[3] not in self.category.listAllCategories():
                    #print 'category removed: ', prno[3]
                    continue
                
                # Discard scope details
                PR = str(prno[0]).split('-')[0]
                
                # Add unique PRs
                if not PRdict.has_key(PR):
                    PRdict[PR] = str(prno[1])
            
            return PRdict
        except gnats.GnatsException, err:
            print "Error in query: %s" % err.message
            return 0
            
