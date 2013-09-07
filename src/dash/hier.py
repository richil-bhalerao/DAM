'''
Created on Jun 12, 2013

@author: richilb
'''

#!/usr/bin/python
import os

class Hier(object):
    
    '''
    Builds a multi-valued hash where key is a manager and value is a list of immediate reports.
    empdict is the dictionary that stores the above key, value pair
    '''
    def __init__(self):
        self.empdict = {}

        subfldlist = list()
        for line in os.popen("/usr/local/bin/query-pr --subfields 'responsible'"):
            subfldlist.append(line.rstrip('\n'))
        
        reportIDX = subfldlist.index('username')
        managerIDX = subfldlist.index('manager')
        
        for line in os.popen("/usr/local/bin/query-pr --adm-field responsible --adm-subfield-search bu --adm-key '..*'"):
            line = line.rstrip('\n')
            arr = line.split(":")
            report = arr[reportIDX]
            manager = arr[managerIDX]
            self.empdict.setdefault(manager, []).append(report)
    
    
    '''
    Recursively traverses through the employee dictionary to return the hierarchy of reporting members of a particular manager.
    '''
    def __all_reports(self, manager, reportslist):
        nextlevelreports = self.reports(manager, 1)
        if nextlevelreports is not None:
            for report in nextlevelreports:
                reportslist.append(report)
                if self.reports(report, 1) is not None:
                    self.__all_reports(report, reportslist)
                else:
                    continue
                
        return reportslist
    
    '''
    reports(manager , directflag)

    =>  Get all reports under a given manager.
      Arguments:
        Username of manager whose employees below him we want (REQUIRED)
        Flag (0 or 1) to get all reports or only get direct reports
      Returns:
        Sorted list of username strings
      Example:
        all_reports = reports("sofiane", 0);     
        direct_reports = reports("sofiane", 1); 
    '''
    def reports(self, manager, flag):
        try:
            if flag == 1:
                return sorted(self.empdict[manager], key=str.lower)
            elif flag == 0:
                return sorted(self.__all_reports(manager, []), key=str.lower)
            else:
                return None
        except KeyError:
            return None
    
    '''
    managers(manager , directflag)

    =>  Get all managers under a given manager.
      Arguments:
        Username of manager whose managers below him we want (REQUIRED)
        Flag (0 or 1) to all reporting managers or only get direct reporting managers.
      Returns:
        Sorted list of username strings
      Example:
        To get all managers under sofiane:
        managers = managers("sofiane", 0);
        To get all direct reports of sofiane who are managers:
        reporting_managers = managers("sofiane", 1);
    '''
    def managers(self, manager, flag):
        try:
            submanagerslist = list()
            for submgr in self.reports(manager, flag):
                if self.reports(submgr, 1) is not None:
                    submanagerslist.append(submgr)
                        
            return sorted(submanagerslist, key=str.lower)
        except:
            return None
            

    '''
    manager()
    => Get the manager of a person.
      Arguments:
        Username of person whose manager we want to return. (REQUIRED)
      Returns:
        string with username of manager, or None
      Example:
        To get the boss of a person:
        mgr = manager("alex");
    '''
    def manager(self, username):
        for manager, reports in self.empdict.items():
            if username in reports:
                return manager
        
    '''
    unmanaged()

    =>  Get all people that do not have a manager listed
      Arguments: N/A
      Returns:
        sorted list of username strings 
      Example:
        To get all people in the system who do not have a manager listed:
        unmanaged = unmanaged();
    '''
    def unmanaged(self):
        return sorted(self.reports('', 1), key=str.lower)
    
    
    '''
    unmanaged_managers()

      Get all people who are managers but do not themselves have a manager listed
      Arguments: N/A
      Returns:
        Sorted list of username strings 
      Example:
        To get all managers in the system who do not have a manager listed:
        @unmanaged_mgrs = unmanaged_managers();
    '''
    def unmanaged_managers(self):
        unmanagedmgrlist = list()
        for manager, reports in self.empdict.items():
            if self.manager(manager) is None  and manager != '':
                unmanagedmgrlist.append(manager)
        
        return sorted(unmanagedmgrlist, key=str.lower)
    