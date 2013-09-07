'''
Created on Jun 12, 2013

@author: richilb
'''

from scrape import Scrape
from emailalert import EmailAlert
from rule import Rule
import logging
import datetime


class Verify(object):
    
    # Initialize the logpath and server name obtained from the config file
    def __init__(self, logpath, server):
        self.logpath = logpath
        self.timestamp = ''    # Time stamp will be updated when the file is created
        self.scrape = Scrape(server)
        self.rule = Rule()
    
    # Send an email by refering to the dictionary that includes list of users for which discrepancy was found for particular rule type
    def sendEmail(self, UserRuleDict):
        # Send an email if at least one discrepancy was found
        msgbody = ''
        if len(UserRuleDict) > 0:
            for rule, userlist in UserRuleDict.items():
                msgbody += ' \n\n*** Dashboard data does not match GNATS for rule type %(1)s for following users: *** \n%(2)s' \
                % {"1": rule, "2": ', '.join(user for user in userlist)} 
                
            msgbody += '\n\nRefer to the following log file for details: \n%s/DAM_%s.log' % (self.logpath, self.timestamp) 
            EmailAlert().send('dashboard-poc@juniper.net', 
                              ['dashboard-dev@juniper.net'], 
                              'DAM Alert', msgbody)
    
    '''
    Run the logic to compare the list of PRs found in Dashboard and the one generated from Gnats
    Log all the details and if discrepancy is found, send and email alert to concerned users
    '''    
    def run(self, usernamelist, rulelist):
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logfile = '%s/DAM_%s.log' % (self.logpath, self.timestamp)
        logging.basicConfig(filename=logfile, filemode='w', format='%(message)s' ,level=logging.WARNING)
        hdlr = logging.FileHandler(logfile)
        try:
            discrepancyUserdict = {}
            for ruletype in rulelist:
                for user in usernamelist:
                    logline = '-----------------------------------------------------------------------------------'
                    print logline
                    logging.critical(logline)
                    
                    logline = 'Verifying for user ||%(1)s|| for ||%(2)s|| type of PRs: ' % {"1": user, "2": ruletype}
                    print logline
                    logging.critical(logline)
                    
                    gnatsPRlist = self.rule.getPRlist(user, ruletype)
                    dashPRlist = self.scrape.getPRList(user, ruletype)
                    
                    discrepancylist1 = list(set(gnatsPRlist) - set(dashPRlist))
                    discrepancylist2 = list(set(dashPRlist) - set(gnatsPRlist))
                    
                    logging.critical('%s:' % datetime.datetime.now().strftime("%A, %d - %B %Y %I:%M%p"))
                    logline = 'Count of PRs from GNATS: %d' % len(gnatsPRlist)
                    print logline
                    logging.critical(logline)
                    
                    logline = 'Count of PRs from Dashboard: %d' % len(dashPRlist)
                    print logline
                    logging.critical(logline)
                    
                    logline = 'List of PRs missing in dashboard: [%s] ' % ','.join(d for d in discrepancylist1)
                    print logline
                    logging.critical(logline)
                    
                    logline = 'List of PRs additionally found in dashboard: [%s]' % ','.join(d for d in discrepancylist2)
                    print logline
                    logging.critical(logline)
                    
                    if len(discrepancylist1 + discrepancylist2) > 0:
                        print 'Checking for recently updated PRs and discarding false negatives from the list...'
                        finalDescList = self.removeRecentPRs(discrepancylist1 + discrepancylist2)
                        if len(finalDescList) > 0:
                            logline = '\nDiscrepancies found after removing recently updated PRs: [%s] ' % ','.join(f for f in finalDescList)
                            discrepancyUserdict.setdefault(ruletype, []).append(user)
                        else:
                            logline = '\nDiscrepancies found after removing recently updated PRs: None'
                        print logline
                        logging.critical(logline)
                    else:
                        logline = '\nNo discrepancies found at all'
                        print logline
                        logging.critical(logline)
            
            
            # alert admin by sending an autogenerated email:
            if len(discrepancyUserdict) > 0:
                self.sendEmail(discrepancyUserdict)
            
            # close the log file
            hdlr.close()
        except Exception, e:
            logging.exception(e)
    
    # Discard the PRs for which updates are not yet reflected on Dashboard UI. 
    def removeRecentPRs(self, PRlist):
        PRdict = self.rule.getPRdict(PRlist)
        PRlist = []
        for PR, LMD in PRdict.items():
            lastModifiedTime = datetime.datetime.strptime(LMD, '%Y-%m-%d %H:%M:%S %Z')
            lastDashbrdUpdateTime = self.scrape.getUpdatedTimeFromUI() - datetime.timedelta(hours=2)
            #print PR + ' | ' + str(lastModifiedTime) + ' | ' + str(lastDashbrdUpdateTime)
            if (lastModifiedTime < lastDashbrdUpdateTime):
                PRlist.append(PR)
                    
        return PRlist    

