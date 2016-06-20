'''
This module implements evaluation methods used to evaluate rules defined in
the input YAML file.
'''
from ruleset import EvalResult, MethodProvider


class StringMatch(MethodProvider):
    '''
    Implements a string matching rule for CiscoConfParse objects. Supports the
    following parameters for different kinds of matching.

    Mandatory
    ---------
    All mandatory conditions that are found in the selection will create an
    EvalResult object with result='pass'. If a mandatory condition is not
    found in the selection an EvalResult object with result='fail' will be
    created.

    Permitted
    ---------
    All permitted conditions that are found in the selection will create an
    EvalResult object with result='pass'. No EvalResult object is created for
    conditions that are not found in the selection.

    Forbidden
    ---------
    All forbidden conditions that are found in the selection will create an
    EvalResult object with result='fail'. No EvalResult object is created for
    conditions that are not found in the selection.
    '''

    # used by get_plugin() to find the correct plugin to run when evaluating
    # the ruleset
    method_name = 'string_match'

    def __init__(self, rule):
        self.mandatory = rule.params.get('mandatory')
        self.permitted = rule.params.get('permitted')
        self.forbidden = rule.params.get('forbidden')
        self.rule = rule
        self.eval_result = []
        self.verified = False

    def verify(self):
        '''
        Raise an exceptions if any of the supported rule param keys have an invalid
        value, or there are unsupported params specified in the rule.
        '''

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

    def apply(self):
        '''
        Using the regex in *self.rule.selection*, configuration from the relevant
        ccp objects will be selected and evaluated to see if they match any of the
        conditions that present in the supported parameters..
        '''

        # If self.verify() has not been called, do it now to verify that
        # input parameters are valid.
        if self.verified == False:
            self.verify()

        configs = self.rule.parent.configs

        # Evaluate for each supported input parameter.
        for config in configs:
            if self.mandatory:
                self.eval_mandatory(config)
            if self.permitted:
                self.eval_permitted(config)
            if self.forbidden:
                self.eval_forbidden(config)

        return self.eval_result

    def eval_mandatory(self, config):
        '''
        For all conditions in self.mandatory, evaluate if condition is found
        in obj, create EvalResult objects accordingly and add them to
        *self.eval_result*. Add all lines with matching conditions to
        *config.matched_lines*.
        '''

        objs = config.ccp_obj.find_objects(self.rule.selection)
        mandatory = set(self.mandatory)

        # *objs* can contain obj w/ children and/or obj w/o children. we need
        # to handle the two cases separately due to the way CiscoConfParse
        # searches in obj's w/ and w/o children.
        obj_w_children = [obj for obj in objs if obj.children]
        obj_wo_children = set(objs) - set(obj_w_children)

        if obj_w_children:
            for obj in obj_w_children:
                found = set()
                for condition in mandatory:
                    match = obj.re_search_children(condition)
                    if match:
                        found.add(condition)
                        config.matched_lines.extend(match)
                        self.eval_result.append(EvalResult(result='pass',
                                                           rule=self.rule,
                                                           param='mandatory',
                                                           config=config.filename,
                                                           cfgline=[obj],
                                                           condition=condition))
                # find all conditions that were not found in this obj's
                # children.
                missing = mandatory - found
                for condition in missing:
                    self.eval_result.append(EvalResult(result='fail',
                                                       rule=self.rule,
                                                       param='mandatory',
                                                       config=config.filename,
                                                       cfgline=[obj],
                                                       condition=condition))

        if obj_wo_children:
            found = set()
            for obj in obj_wo_children:
                for condition in mandatory:
                    match = obj.re_search(condition)
                    if match:
                        found.add(condition)
                        config.matched_lines.append(obj)
                        self.eval_result.append(EvalResult(result='pass',
                                                           rule=self.rule,
                                                           param='mandatory',
                                                           config=config.filename,
                                                           cfgline=[obj],
                                                           condition=condition))
            # find all conditions that were not found in this obj's
            # children.
            missing = mandatory - found
            for condition in missing:
                self.eval_result.append(EvalResult(result='fail',
                                                   rule=self.rule,
                                                   param='mandatory',
                                                   config=config.filename,
                                                   condition=condition))

    def eval_permitted(self, config):
        '''
        For all conditions in self.permitted, evaluate if condition is found
        in obj, create EvalResult objects accordingly and add them to
        *self.eval_result*. Add all lines with matching conditions to
        *config.matched_lines*.
        '''

        objs = config.ccp_obj.find_objects(self.rule.selection)
        permitted = set(self.permitted)

        # *objs* can contain obj w/ children and/or obj w/o children. we need
        # to handle the two cases separately due to the way CiscoConfParse
        # searches in obj's w/ and w/o children.
        obj_w_children = [obj for obj in objs if obj.children]
        obj_wo_children = set(objs) - set(obj_w_children)

        if obj_w_children:
            for obj in obj_w_children:
                found = set()
                for condition in permitted:
                    match = obj.re_search_children(condition)
                    if match:
                        found.add(condition)
                        config.matched_lines.extend(match)
                        self.eval_result.append(EvalResult(result='pass',
                                                           rule=self.rule,
                                                           param='permitted',
                                                           config=config.filename,
                                                           condition=condition))

        if obj_wo_children:
            found = set()
            for obj in obj_wo_children:
                for condition in permitted:
                    match = obj.re_search(condition)
                    if match:
                        found.add(condition)
                        config.matched_lines.append(obj)
                        self.eval_result.append(EvalResult(result='pass',
                                                           rule=self.rule,
                                                           param='permitted',
                                                           config=config.filename,
                                                           condition=condition))

    def eval_forbidden(self, config):
        '''
        For all conditions in self.forbidden, evaluate if condition is found
        in obj, create EvalResult objects accordingly and add them to
        *self.eval_result*. Add all lines with matching conditions to
        *config.matched_lines*.
        '''

        objs = config.ccp_obj.find_objects(self.rule.selection)
        forbidden = set(self.forbidden)

        # *objs* can contain obj w/ children and/or obj w/o children. we need
        # to handle the two cases separately due to the way CiscoConfParse
        # searches in obj's w/ and w/o children.
        obj_w_children = [obj for obj in objs if obj.children]
        obj_wo_children = set(objs) - set(obj_w_children)

        if obj_w_children:
            for obj in obj_w_children:
                found = set()
                for condition in forbidden:
                    match = obj.re_search_children(condition)
                    if match:
                        found.add(condition)
                        config.matched_lines.extend(match)
                        self.eval_result.append(EvalResult(result='fail',
                                                           rule=self.rule,
                                                           param='forbidden',
                                                           config=config.filename,
                                                           condition=condition))

        if obj_wo_children:
            found = set()
            for obj in obj_wo_children:
                for condition in forbidden:
                    match = obj.re_search(condition)
                    if match:
                        found.add(condition)
                        config.matched_lines.append(obj)
                        self.eval_result.append(EvalResult(result='fail',
                                                           rule=self.rule,
                                                           param='forbidden',
                                                           config=config.filename,
                                                           condition=condition))

class CompareSubIfs(MethodProvider):
    '''
    Implements a subif matching rule for CiscoConfParse objects.
    No parameters are supported by this rule method at this point.
    '''

    # used by get_plugin() to find the correct plugin to run when evaluating
    # the ruleset
    method_name = 'compare_subifs'

    def __init__(self, rule):
        self.rule = rule
        self.eval_result = []
        self.verified = False

    def verify(self):
        '''Verify that no parameters are configured for this rule'''
        if self.rule.params is not None:
            raise RuleParamUnsupported(self.rule.params.keys())
        self.verified = True

    def apply(self):
        '''
        Using the regex in *self.rule.selection*, configuration from the relevant
        ccp objects will be selected and evaluated to verify that they all
        contain the same subinterfaces. If a subinterface is missing from any
        of the configs, an EvalResult object with result='fail' will be created.
        '''

        # If self.verify() has not been called, do it now to verify that
        # input parameters are valid.
        if self.verified == False:
            self.verify()

        configs = self.rule.parent.configs

        # first populate *all_subifs*
        all_subifs = set()
        for config in configs:
            objs = config.ccp_obj.find_objects(self.rule.selection)
            for obj in objs:
                subif = int(obj.text.partition('.')[2])
                all_subifs.add(subif)

        # now check which subif is missing in which config
        # and create an EvalResult object for them
        for config in configs:
            objs = config.ccp_obj.find_objects(self.rule.selection)
            config_subifs = {}
            for obj in objs:
                subif = int(obj.text.partition('.')[2])
                config_subifs[subif] = obj
            for subif in all_subifs:
                if not subif in config_subifs.keys():
                    self.eval_result.append(
                        EvalResult(result='fail',
                                   config=config.filename,
                                   rule=self.rule,
                                   msg="subif {} missing".format(subif)))
        return self.eval_result
