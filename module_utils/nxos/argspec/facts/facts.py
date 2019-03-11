class FactsArgs(object):

    def __init__(self, **kwargs):
        pass

    choices = [
        'all',
        'l2_interfaces',
    ]

    argument_spec = {
        'gather_subset': dict(default=['!config'], type='list'),
        'gather_network_resources': dict(default=['all'], choices=choices, type='list'),
    }
