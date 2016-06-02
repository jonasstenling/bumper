'''
This module is used to test the project implementation from the command
line
'''
from ruleset import RuleSet
from ciscoconfparse import CiscoConfParse

def load_config(config_file):
    '''Returns parse configuration as CiscoConfParse object.'''
    return CiscoConfParse(config_file)

def main():
    '''Main entry point for module.'''

    config = load_config('test.conf')
    myrules = RuleSet()
    myrules.load_rules('compare.yml')
    myrules.verify_rules()
    myresult = []

    for rule in myrules.rules:
        result = rule.apply(config)
        print "*" * 80
        print "*" * 80
        print "*" * 80
        print "Evaluation result for rule '{}':".format(rule.name)
        for element in result:
            if element.result == False:
                print " Method: {}".format(element.rule.method)
                print " Param: {}".format(element.param)
                print " Condition: {}".format(element.condition)
                cfglines = []
                parent = None
                for i in element.cfgline:
                    cfglines.append(i.text)
                    if i.parent != i:
                        parent = i.parent.text
                if parent:
                    print " {}".format(parent)
                for i in cfglines:
                    print "  {}".format(i)
                print "*" * 80
        myresult.append(result)
        print " *** End of evaluation result ***"
    return myresult

if __name__ == '__main__':
    main()
