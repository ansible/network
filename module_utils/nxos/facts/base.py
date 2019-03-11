import re

from copy import deepcopy

from ansible.module_utils.six import iteritems


class FactsBase(object):

    generated_spec = {}
    ansible_facts = {'ansible_network_resources': {}}

    def __init__(self, argspec, subspec=None, options=None):
        spec = deepcopy(argspec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = self.generate_dict(facts_argument_spec)

    def generate_dict(self, spec):
        """
        Generate dictionary which is in sync with argspec

        :param spec: A dictionary which the argspec of module
        :rtype: A dictionary
        :returns: A dictionary in sync with argspec with default value
        """
        obj = {}
        if not spec:
            return obj

        for k, v in iteritems(spec):
            if 'default' in v:
                d = {k: v['default']}
            elif 'type' in v and v['type'] == 'dict':
                d = {k: self.generate_dict(v['options'])}
            else:
                d = {k: None}
            obj.update(d)

        return obj

    def parse_conf_arg(self, cfg, arg):
        """
        Parse config based on argument

        :param cfg: A text string which is a line of configuration.
        :param arg: A text string which is to be matched.
        :rtype: A text string
        :returns: A text string if match is found
        """
        match = re.search(r'%s (.+)(\n|$)' % arg, cfg, re.M)
        if match:
            return match.group(1).strip()

    def parse_conf_cmd_arg(self, cfg, cmd, res1, res2=None):
        """
        Parse config based on command

        :param cfg: A text string which is a line of configuration.
        :param cmd: A text string which is the command to be matched
        :param res1: A text string to be returned if the command is present
        :param res2: A text string to be returned if the negate command is present
        :rtype: A text string
        :returns: A text string if match is found
        """
        match = re.search(r'\n\s+%s(\n|$)' % cmd, cfg)
        if match:
            return res1
        else:
            if res2 is not None:
                match = re.search(r'\n\s+no %s(\n|$)' % cmd, cfg)
                if match:
                    return res2

    def generate_final_config(self, cfg_dict):
        """
        Generate final config dictionary

        :param cfg_dict: A dictionary parsed in the facts system
        :rtype: A dictionary
        :returns: A dictionary by elimating keys that have null values
        """
        final_cfg = {}
        if not cfg_dict:
            return final_cfg

        for key, val in iteritems(cfg_dict):
            dct = None
            if isinstance(val, dict):
                child_val = self.generate_final_config(val)
                if child_val:
                    dct = {key: child_val}
            elif val:
                dct = {key: val}
            if dct:
                final_cfg.update(dct)
        return final_cfg
