'''
Implements ruleset parsing
'''
import yaml
from method import MethodProvider


class Rule:
    '''Represents a Rule as defined in the input YAML file.'''
    def __init__(self, rule, parent):
        self.name = rule.get('name')
        self.method = rule.get('method')
        self.selection = rule.get('selection')
        self.params = rule.get('params')
        self.parent = parent

    def __repr__(self):
        return "Rule(name='{}', method='{}', selection='{}', params='{}'".format(
            self.name,
            self.method,
            self.selection,
            self.params)

    def apply(self, config):
        plugin = MethodProvider.get_plugin(self)
        return plugin.apply(config)

    def verify(self):
        plugin = MethodProvider.get_plugin(self)
        return plugin.verify()

class RuleSet:
    '''Support class to load YAML input file and create Rule objects.'''
    def __init__(self):
        self.rules = []
        self.configs = []

    def load_rules(self, rule_file):
        '''Load rules from YAML file.'''
        with open(rule_file, 'r') as f:
            yaml_file = yaml.load(f)
            configs = yaml_file.get('configs')
            if configs:
                self.configs = configs
            includes = yaml_file.get('include')
            if includes:
                for i in includes:
                    self.load_rules(i)
            ruleset = yaml_file.get('ruleset')
            if ruleset:
                for rule in yaml_file['ruleset']:
                    if isinstance(rule, dict):
                        self.add_rule(rule)

    def verify_rules(self):
        for rule in self.rules:
            rule.verify()

    def add_rule(self, rule):
        '''Append rule to RuleSet.'''
        self.rules.append(Rule(rule, self))
