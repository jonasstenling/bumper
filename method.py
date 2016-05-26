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
        self.mandatory = None
        self.permitted = None
        self.forbidden = None
        self.only = None
        self.evaluation = []
        self.rule = None
        self.config = None

    def __call__(self, rule, config):
        '''
        Returns: List of EvalResult objects.

        Parameters:
            rule    Rule object to be evaluated.
            config  CiscoConfParse object containing the configuration to
                    evaluate.
        '''

        self.mandatory = rule.params.get('mandatory')
        self.permitted = rule.params.get('permitted')
        self.forbidden = rule.params.get('forbidden')
        self.only = rule.params.get('only')
        self.evaluation = []
        self.rule = rule
        self.config = config

        if self.mandatory:
            self.eval_mandatory()
        if self.permitted:
            self.eval_permitted()
        if self.forbidden:
            self.eval_forbidden()
        if self.only:
            self.eval_only()

        self.cleanup()


        return self.evaluation

    def eval_mandatory(self):
        '''
        Evaluate param *mandatory* and append EvalResult objects when
        matching. Delete all matching lines from config object.
        '''

        objs = self.config.find_objects(self.rule.selection)
        for obj in objs:
            if obj.children:
                for i in self.mandatory:
                    match = obj.delete_children_matching(i)
                    if match:
                        self.evaluation.append(EvalResult(result=True, cfgline=[obj],
                                                          rule=self.rule,
                                                          param='mandatory',
                                                          condition=i))
                    else:
                        self.evaluation.append(EvalResult(result=False, cfgline=[obj],
                                                          rule=self.rule,
                                                          param='mandatory',
                                                          condition=i))
            else:
                for i in self.mandatory:
                    match = obj.re_search(i)
                    if match:
                        self.evaluation.append(EvalResult(result=True, cfgline=[obj],
                                                          rule=self.rule,
                                                          param='mandatory',
                                                          condition=i))
                        obj.delete()
                    else:
                        self.evaluation.append(EvalResult(result=False,
                                                          cfgline=[obj], rule=self.rule,
                                                          param='mandatory',
                                                          condition=i))
        self.config.commit()

    def eval_permitted(self):
        '''
        Evaluate param *permitted* and append EvalResult objects when
        matching. Delete all matching lines from config object.
        '''

        objs = self.config.find_objects(self.rule.selection)
        for obj in objs:
            if obj.children:
                for i in self.permitted:
                    match = obj.delete_children_matching(i)
                    if match:
                        self.evaluation.append(EvalResult(result=True, cfgline=[obj],
                                                          rule=self.rule,
                                                          param='permitted',
                                                          condition=i))
            else:
                for i in self.permitted:
                    match = obj.re_search(i)
                    if match:
                        self.evaluation.append(EvalResult(result=True, cfgline=[obj],
                                                          rule=self.rule,
                                                          param='permitted',
                                                          condition=i))
                        obj.delete()
        self.config.commit()

    def eval_forbidden(self):
        '''
        Evaluate param *forbidden* and append EvalResult objects when
        matching. Delete all matching lines from config object.
        '''

        objs = self.config.find_objects(self.rule.selection)
        for obj in objs:
            if obj.children:
                for i in self.forbidden:
                    match = obj.delete_children_matching(i)
                    if match:
                        self.evaluation.append(EvalResult(result=False, cfgline=[obj],
                                                          rule=self.rule,
                                                          param='forbidden',
                                                          condition=i))
            else:
                for i in self.forbidden:
                    match = obj.re_search(i)
                    if match:
                        self.evaluation.append(EvalResult(result=False, cfgline=[obj],
                                                          rule=self.rule,
                                                          param='forbidden',
                                                          condition=i))
                        obj.delete()
        self.config.commit()

    def eval_only(self):
        '''
        Evaluate param *only* and append EvalResult objects when
        matching. This param will match all remaining config lines matched by
        self.rule.selection and create an EvalResult object with them.
        '''
        objs = self.config.find_objects(self.rule.selection)
        if len(objs) > 1:
            for obj in objs:
                if obj.children:
                    self.evaluation.append(EvalResult(result=False,
                                                      cfgline=obj.children,
                                                      rule=self.rule,
                                                      param='only',
                                                      condition=''))

    def cleanup(self):
        '''
        When all evaluation has been done, find all objects matching
        self.rule.selection that are still in config but without any children
        and delete them. This is done to avoid e.g. having an interface being
        evaluated repeatedly when all its config lines have already been
        verified.
        '''

        objs = self.config.find_objects(self.rule.selection)
        for obj in objs:
            if not obj.children:
                obj.delete()
        self.config.commit()
