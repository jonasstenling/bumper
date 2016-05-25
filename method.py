'''
This module implements evaluation methods used to evaluate rules defined in
the input YAML file.
'''
from eval import EvalResult

class PluginMount(type):
    '''
    Metaclass used by MethodProvider to create plugin architecture.
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

    def get_plugin(cls, method, *args, **kwargs):
        '''Fetches plugin for *method* and returns the result.'''
        for plugin in cls.plugins:
            if plugin.method_name == method:
                return plugin(*args, **kwargs)

class MethodProvider:
    '''
    Mount point for plugins which refer to Rule evaluation to be performed.
    '''
    def __init__(self):
        pass
    __metaclass__ = PluginMount

class StringMatch(MethodProvider):
    '''
    Implements a string matching rule for CiscoConfParse objects.
    '''

    method_name = 'string_match'

    def __init__(self):
        MethodProvider.__init__(self)

    def __call__(self, rule, config):
        '''
        Returns: List of EvalResult objects.

        Parameters:
            rule    Rule object to be evaluated.
            config  CiscoConfParse object containing the configuration to
                    evaluate.
        '''
        mandatory = rule.params.get('mandatory')
        objs = config.find_objects(rule.selection)

        evaluation = []

        for obj in objs:
            if obj.children:
                for i in mandatory:
                    match = obj.re_search_children(i)
                    if match:
                        evaluation.append(EvalResult(result=True, cfgline=obj,
                                                     rule=i))
                    else:
                        evaluation.append(EvalResult(result=False, cfgline=obj,
                                                     rule=i))
            else:
                for i in mandatory:
                    match = obj.re_search(i, default=None)
                    if match:
                        evaluation.append(EvalResult(result=True, cfgline=obj,
                                                     rule=i))
                    else:
                        evaluation.append(EvalResult(result=False,
                                                     cfgline=obj, rule=i))
        return evaluation

