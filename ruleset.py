'''
Implements ruleset parsing
'''
import yaml
from method import MethodProvider


class Rule:
    '''Represents a Rule as defined in the input YAML file.'''
    def __init__(self, rule):
        self.name = rule.get('name')
        self.method = rule.get('method')
        self.selection = rule.get('selection')
        self.params = rule.get('params')

    def __repr__(self):
        return "Rule(name='{}', method='{}', selection='{}', params='{}'".format(
            self.name,
            self.method,
            self.selection,
            self.params)

    def apply(self, config):
        plugin = MethodProvider.get_plugin(self.method)
        return plugin(self, config)

class RuleSet:
    '''Support class to load YAML input file and create Rule objects.'''
    def __init__(self):
        self.rules = []

    def load_rules(self, rule_file):
        '''Load rules from YAML file.'''
        with open(rule_file, 'r') as f:
            yaml_file = yaml.load(f)
            includes = yaml_file.get('include')
            if includes:
                for i in includes:
                    self.load_rules(i)
            ruleset = yaml_file.get('ruleset')
            if ruleset:
                for rule in yaml_file['ruleset']:
                    if isinstance(rule, dict):
                        self.add_rule(rule)

    def add_rule(self, rule):
        '''Append rule to RuleSet.'''
        self.rules.append(Rule(rule))
