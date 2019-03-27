from ansible.module_utils.network.argspec.base import ArgspecBase

class FactsArgs(ArgspecBase):

    choices = [
        'all',
        'net_configuration_interfaces',
    ]

    argument_spec = {
        'gather_subset': dict(default=['all'], choices=choices, type='list')
    }
