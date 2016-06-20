#!/usr/bin/env python
'''
This module is used to test the project implementation from the command
line
'''
from ruleset import RuleSet
import method_plugins
import sys
import os.path

def main():
    '''Main entry point for module.'''

    myrules = RuleSet()
    myrules.load_rules(sys.argv[1])
    myrules.verify_rules()
    myresult = []

    for rule in myrules.rules:
        result = rule.apply()
        print ">>> Evaluating rule '{}'...".format(rule.name)
        for element in result:
            if element.result == 'fail':
                print "Rule '{}':".format(rule.name)
                print " Result '{}':".format(element.result)
                print " Method: {}".format(element.rule.method)
                print " Config: {}".format(element.config)
                if element.param is not None: print " Param: {}".format(element.param)
                if element.cfgline:
                    cfglines = []
                    parent = None
                    for i in element.cfgline:
                        cfglines.append(i.text)
                        if i.parent != i:
                            parent = i.parent.text
                    if parent:
                        print " Missing in subconfiguration:"
                        print "  {}".format(parent)
                        for i in cfglines:
                            print "   {}".format(i)
                    else:
                        for i in cfglines:
                            print " Missing in subconfiguration:"
                            print "   {}".format(i)
                print " Condition: {}".format(element.condition)
                print " Msg: {}".format(element.msg)
                print " +++"
        myresult.append(result)
        print " *** End of evaluation result ***"
    return myresult

if __name__ == '__main__':
    main()
