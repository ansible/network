from ansible.module_utils.six import iteritems


class ArgspecBase(object):

    argument_spec = {}

    def __init__(self, **kwargs):
        self.values = {}

        for key, value in iteritems(kwargs):
            if key in self.argument_spec:
                setattr(self, key, value)

    def __getattr__(self, key):
        if key in self.argument_spec:
            return self.values.get(key)

    def __setattr__(self, key, value):
        if key in self.argument_spec:
            if value is not None:
                self.values[key] = value
        else:
            super(ArgspecBase, self).__setattr__(key, value)
