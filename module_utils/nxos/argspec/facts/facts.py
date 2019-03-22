from ansible.module_utils.network.argspec.base import ArgspecBase

class FactsArgs(ArgspecBase):

    argument_spec = {
        'gather_subset': dict(default=['all'], type='list')
    }
