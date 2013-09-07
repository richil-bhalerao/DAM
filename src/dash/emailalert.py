'''
Created on Jul 3, 2013

@author: richilb
'''

import smtplib
from smtplib import SMTPException
import email


class EmailAlert(object):
    
    def __init__(self, smtpserver = None):
        if smtpserver == None:
            smtpserver = 'smtp.juniper.net'
        
        self.smtpObj = smtplib.SMTP(smtpserver)
        
        
    def send(self, sender, receivers, subject, body):
        try:
            message = "From: %s \nTo: %s \nSubject: %s \n\n%s\n" % (sender, ', '.join(receivers), subject, body)
            self.smtpObj.sendmail(sender, receivers, message)         
        except SMTPException:
            print "Error: unable to send email"
        


