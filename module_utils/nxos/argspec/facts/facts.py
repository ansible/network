class FactsArgs(object):

    def __init__(self, **kwargs):
        pass

    choices = [
        'all',
        'net_configuration_interfaces',
    ]

    argument_spec = {
        'gather_subset': dict(default=['all'], choices=choices, type='list')
    }
