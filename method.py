'''
This module implements evaluation methods used to evaluate rules defined in
the input YAML file.
'''
from eval import EvalResult

class RuleParamError(Exception):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        return "Param '{}' has invalid value '{}'".format(self.key, self.value)

class RuleParamUnsupported(Exception):
    def __init__(self, keys):
        self.keys = keys

    def __str__(self):
        return "{}".format(self.keys)

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

    def get_plugin(cls, rule, *args, **kwargs):
        '''Fetches plugin for *method* and returns the result.'''
        for plugin in cls.plugins:
            if plugin.method_name == rule.method:
                return plugin(rule, *args, **kwargs)

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

    def __init__(self, rule):
        MethodProvider.__init__(self)
        self.mandatory = rule.params.get('mandatory')
        self.permitted = rule.params.get('permitted')
        self.forbidden = rule.params.get('forbidden')
        self.only = rule.params.get('only')
        self.rule = rule
        self.evaluation = []
        self.verified = False

    def verify(self):
        '''Verify that supported rule keys have the correct value'''

        params = self.rule.params.copy()

        for key, value in self.rule.params.iteritems():
            if key in ('mandatory',
                       'permitted',
                       'forbidden'):
                if isinstance(value, list):
                    for i in value:
                        if not isinstance(i, str):
                            raise RuleParamError(key, i)
                    params.pop(key)
                else:
                    raise RuleParamError(key, value)
            elif key in 'only':
                if isinstance(value, bool):
                    params.pop(key)
                else:
                    raise RuleParamError(key, value)
        # Any key still in *params* is not supported.
        if params.keys():
            raise RuleParamUnsupported(params.keys())

        self.verified = True

    def apply(self, config):
        '''
        Returns: List of EvalResult objects.

        Parameters:
            rule    Rule object to be evaluated.
            config  CiscoConfParse object containing the configuration to
                    evaluate.
        '''

        # If self.verify() has not been called, do it now to verify that
        # input parameters are valid.
        if self.verified == False:
            self.verify()

        # Evaluate for each supported input parameter.
        if self.mandatory:
            self.eval_mandatory(config)
        if self.permitted:
            self.eval_permitted(config)
        if self.forbidden:
            self.eval_forbidden(config)
        if self.only:
            self.eval_only(config)

        self.cleanup(config)

        return self.evaluation

    def eval_mandatory(self, config):
        '''
        Evaluate param *mandatory* and append EvalResult objects when
        matching. Delete all matching lines from config object.
        '''

        objs = config.find_objects(self.rule.selection)
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
        config.commit()

    def eval_permitted(self, config):
        '''
        Evaluate param *permitted* and append EvalResult objects when
        matching. Delete all matching lines from config object.
        '''

        objs = config.find_objects(self.rule.selection)
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
        config.commit()

    def eval_forbidden(self, config):
        '''
        Evaluate param *forbidden* and append EvalResult objects when
        matching. Delete all matching lines from config object.
        '''

        objs = config.find_objects(self.rule.selection)
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
        config.commit()

    def eval_only(self, config):
        '''
        Evaluate param *only* and append EvalResult objects when
        matching. This param will match all remaining config lines matched by
        self.rule.selection and create an EvalResult object with them.
        '''
        objs = config.find_objects(self.rule.selection)
        if len(objs) > 1:
            for obj in objs:
                if obj.children:
                    self.evaluation.append(EvalResult(result=False,
                                                      cfgline=obj.children,
                                                      rule=self.rule,
                                                      param='only',
                                                      condition=''))

    def cleanup(self, config):
        '''
        When all evaluation has been done, find all objects matching
        self.rule.selection that are still in config but without any children
        and delete them. This is done to avoid e.g. having an interface being
        evaluated repeatedly when all its config lines have already been
        verified.
        '''
        objs = config.find_objects(self.rule.selection)
        for obj in objs:
            if not obj.children:
                obj.delete()
        config.commit()

class CompareConfigs(MethodProvider):
    '''
    Implements a string matching rule for CiscoConfParse objects.
    '''

    method_name = 'compare_configs'

    def __init__(self, rule):
        MethodProvider.__init__(self)
        self.mandatory = rule.params.get('mandatory')
        self.permitted = rule.params.get('permitted')
        self.forbidden = rule.params.get('forbidden')
        self.only = rule.params.get('only')
        self.rule = rule
        self.evaluation = []
        self.verified = False

    def verify(self):
        '''Verify that supported rule keys have the correct value'''

        params = self.rule.params.copy()

        for key, value in self.rule.params.iteritems():
            if key in ('mandatory',
                       'permitted',
                       'forbidden'):
                if isinstance(value, list):
                    for i in value:
                        if not isinstance(i, str):
                            raise RuleParamError(key, i)
                    params.pop(key)
                else:
                    raise RuleParamError(key, value)
            elif key in 'only':
                if isinstance(value, bool):
                    params.pop(key)
                else:
                    raise RuleParamError(key, value)
        # Any key still in *params* is not supported.
        if params.keys():
            raise RuleParamUnsupported(params.keys())

        self.verified = True

    def apply(self, config):
        '''
        Returns: List of EvalResult objects.

        Parameters:
            rule    Rule object to be evaluated.
            config  CiscoConfParse object containing the configuration to
                    evaluate.
        '''

        # If self.verify() has not been called, do it now to verify that
        # input parameters are valid.
        if self.verified == False:
            self.verify()

        # Evaluate for each supported input parameter.
        if self.mandatory:
            self.eval_mandatory(config)
        if self.permitted:
            self.eval_permitted(config)
        if self.forbidden:
            self.eval_forbidden(config)
        if self.only:
            self.eval_only(config)

        self.cleanup(config)

        return self.evaluation

    def eval_mandatory(self, config):
        '''
        Evaluate param *mandatory* and append EvalResult objects when
        matching. Delete all matching lines from config object.
        '''

        objs = config.find_objects(self.rule.selection)
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
        config.commit()

    def eval_permitted(self, config):
        '''
        Evaluate param *permitted* and append EvalResult objects when
        matching. Delete all matching lines from config object.
        '''

        objs = config.find_objects(self.rule.selection)
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
        config.commit()

    def eval_forbidden(self, config):
        '''
        Evaluate param *forbidden* and append EvalResult objects when
        matching. Delete all matching lines from config object.
        '''

        objs = config.find_objects(self.rule.selection)
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
        config.commit()

    def eval_only(self, config):
        '''
        Evaluate param *only* and append EvalResult objects when
        matching. This param will match all remaining config lines matched by
        self.rule.selection and create an EvalResult object with them.
        '''
        objs = config.find_objects(self.rule.selection)
        if len(objs) > 1:
            for obj in objs:
                if obj.children:
                    self.evaluation.append(EvalResult(result=False,
                                                      cfgline=obj.children,
                                                      rule=self.rule,
                                                      param='only',
                                                      condition=''))

    def cleanup(self, config):
        '''
        When all evaluation has been done, find all objects matching
        self.rule.selection that are still in config but without any children
        and delete them. This is done to avoid e.g. having an interface being
        evaluated repeatedly when all its config lines have already been
        verified.
        '''
        objs = config.find_objects(self.rule.selection)
        for obj in objs:
            if not obj.children:
                obj.delete()
        config.commit()
