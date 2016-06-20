#!/usr/bin/python
'''
Implements ruleset parsing
'''
import yaml
from ciscoconfparse import CiscoConfParse

class RuleParamError(Exception):
    '''Raise when input parameter has an invalid value.'''
    def __init__(self, key, value):
        Exception.__init__()
        self.key = key
        self.value = value

    def __str__(self):
        return "Param '{}' has invalid value '{}'".format(self.key, self.value)

class RuleParamUnsupported(Exception):
    '''Raise when rule has an unsupported parameter defined.'''
    def __init__(self, keys):
        Exception.__init__()
        self.keys = keys

    def __str__(self):
        return "{}".format(self.keys)

class PluginMount(type):
    '''
    Metaclass used by MethodProvider to create plugin architecture.
    For more information please refer to:
    http://martyalchin.com/2008/jan/10/simple-plugin-framework/
    '''
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.plugins = []
        else:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            cls.plugins.append(cls)

    def get_plugin(cls, rule, *args, **kwargs):
        '''Fetches plugin for *rule.method* and returns the result.'''
        for plugin in cls.plugins:
            if plugin.method_name == rule.method:
                return plugin(rule, *args, **kwargs)

class MethodProvider:
    '''
    Inherited by all classes that implements a rule evaluation method.
    By inheriting this class the subclass is registered as a plugin and can be
    looked up for execution when evaluating the ruleset.
    '''
    def __init__(self):
        pass
    __metaclass__ = PluginMount

class Config:
    def __init__(self, filename):
        self.ccp_obj = CiscoConfParse(filename)
        self.filename = filename
        self.matched_lines = []

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

    def apply(self):
        plugin = MethodProvider.get_plugin(self)
        return plugin.apply()

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
                for config in configs:
                    self.configs.append(Config(config))
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

class EvalResult:
    '''
    Parameters:
       result   pass = True, fail = None
       cfgline  reference to IOSCfgLine object.
       rule     reference to Rule object.
    '''
    def __init__(self, result=None, cfgline=None, config=None, rule=None,
                 condition=None, param=None, msg=None):
        self.result = result
        self.cfgline = cfgline
        self.config = config
        self.rule = rule
        self.condition = condition
        self.param = param
        self.msg = msg

