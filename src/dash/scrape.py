'''
Created on Jun 12, 2013

@author: richilb
'''


from bs4 import BeautifulSoup
from login import Login
import datetime, re


class Scrape(object):
    
    def __init__(self, server):
        # initialize server from the config file
        self.server = server
        self.__login = Login()
    
    # decide upon the rule expression that is supposed to be included in the link that will be used to scrape    
    def getRule(self, ruletype):
        if ruletype.lower() == 'test blocker':
            return 'test_blockers'
        elif ruletype.lower() == "regression":
            return 'regression_prs'
        elif ruletype.lower() == "beta blocker":
            return 'beta_blocker_prs'
        elif ruletype.lower() == "cl1":
            return 'CL1'
        elif ruletype.lower() == "cl2":
            return 'CL2'
        elif ruletype.lower() == "il1":
            return 'IL1'
        elif ruletype.lower() == "il2":
            return 'IL2'
    
    # From the list of PRs obtained by scraping dashboard get the count of PRs
    def getCount(self, username, ruletype):
        dashboard = self.__login.getPage('https://%(1)s.juniper.net/dashboard/matrix/?rules=%(2)s&releases=all&users=%(3)s&feedback=yes&found_during=all' \
                                         % {"1": self.server, "2": self.getRule(ruletype), "3": username})
        soup = BeautifulSoup(dashboard)
        table = soup.find( "table", {"id":"matrix-table"} )
        rows = table.findAll('tr')
        tabledata = rows[1].findAll('td') 
        try:
            count = int(tabledata[0].find(text=True))
            return count
        except Exception, err:
            err.message
            return 0
    
    # Get the list of PRs for a particular user and particular rule type
    def getPRList(self, username, ruletype):
        dashboard = self.__login.getPage('https://%(1)s.juniper.net/dashboard/matrix/?rules=%(2)s&releases=all&users=%(3)s&feedback=yes&found_during=all' \
                                         % {"1": self.server, "2": self.getRule(ruletype), "3": username})
        soup = BeautifulSoup(dashboard)
        table = soup.find( "table", {"id":"matrix-table"} )
        rows = table.findAll('tr')
        tabledata = rows[1].findAll('td')
        try:
            PRlist = []
            count = int(tabledata[0].find(text=True))
            if count > 0:
                a = tabledata[0].find(href=True)
                link = a['href']
                if link == '#':
                    # Implies that PR list is big so get the list from the hidden input field
                    docvalue = a["onclick"]
                    r = re.compile('document.(.*?).submit')
                    m = r.search(docvalue)
                    if m:
                        myid = str(m.group(1))
                        myform = soup.find( "form", {"name": myid} )
                        myinput = myform.find("input", {"name": "prs"})
                        PRstring = myinput['value']
                        for PR in PRstring.split(','):
                            PRlist.append(str(PR).split('-')[0])
                else:
                    if count == 1:
                        if 'prs=' in link:              # Implies that count is one but there are several scopes of same PR number
                            r = re.compile('prs=(.*?)&')
                            m = r.search(link)
                            if m:
                                PRstring = m.group(1)
                                for PR in PRstring.split(','):
                                    PRlist.append(str(PR).split('-')[0])
                        else:
                            # Get PR number from the end of URL
                            PR = str(link.rsplit('/',1)[1])
                            PRlist.append(str(PR).split('-')[0])
                    elif count > 1:
                        # Get PR number from the middle of URL
                        r = re.compile('prs=(.*?)&')
                        m = r.search(link)
                        if m:
                            PRstring = m.group(1)
                            for PR in PRstring.split(','):
                                PRlist.append(str(PR).split('-')[0])
            
            # Remove duplicates
            if len(PRlist) > 0:
                PRlist = list(set(PRlist))                
            return PRlist
        except Exception, err:
            err.message
            return []
    
    # Scrape the last updated time which is visible on the dashboard UI. 
    def getUpdatedTimeFromUI(self):
        dashboard = self.__login.getPage('https://%s.juniper.net/dashboard' % self.server)
        soup = BeautifulSoup(dashboard)
        # Look for last  p tag with class = note
        para = soup.findAll( "p", {"class":"note"} )
        line = para[len(para)-1].find(text=True)
        timestampstr = line.split(' ')[1] + ' ' + line.split(' ')[2]
        updatedtimestamp = datetime.datetime.strptime(timestampstr, '%Y-%m-%d %H:%M')
        return updatedtimestamp
