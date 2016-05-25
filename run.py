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
    myrules.load_rules('syntax.yml')
    myresult = []

    for rule in myrules.rules:
        result = rule.apply(config)
        for element in result:
            if element.result == False:
                print "Rule evaluation failed:\n Cfgline: '{}'\n Rule: {}".format(
                    element.cfgline.text,
                    element.rule)
        myresult.append(result)
    return myresult

if __name__ == '__main__':
    main()
