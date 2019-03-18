from ansible.module_utils.argspec.base import ArgspecBase

class FactsArgs(ArgspecBase):

    argument_spec = {
        'gather_subset': dict(default=['all'], type='list')
    }
