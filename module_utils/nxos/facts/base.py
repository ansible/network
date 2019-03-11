from copy import deepcopy

from ansible.module_utils.six import iteritems


class FactsBase(object):

    generated_spec = {}
    data = None

    def __init__(self, data, argspec, subspec=None, options=None):
        self.data = data

        spec = deepcopy(argspec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        generate_spec = self.generate_dict(facts_argument_spec)

    def generate_dict(self, spec):
        obj = {}
        if not spec:
            return obj

        for k, v in iteritems(spec):
            if 'default' in v:
                d = {k: v['default']}
            else:
                d = {k: None}
            obj.update(d)

        return obj
