
'''This module contains classes related to rule evaluation results'''

class EvalResult:
    '''
    Parameters:
       result   pass = True, fail = None
       cfgline  reference to IOSCfgLine object.
       rule     reference to Rule object.
    '''
    def __init__(self, result='pass', cfgline=None, rule=None):
        self.result = result
        self.cfgline = cfgline
        self.rule = rule
