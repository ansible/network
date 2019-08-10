from __future__ import absolute_import, division, print_function
__metaclass__ = type


class FactsArgs(object):  # pylint: disable=R0903
    """ The arg spec for the ios facts module
    """

    def __init__(self, **kwargs):
        pass

    choices = [
        'all',
        'l2_interfaces',
        '!l2_interfaces'
    ]

    argument_spec = {
        'gather_subset': dict(default=['!config'], type='list'),
        'gather_network_resources': dict(choices=choices, type='list'),
    }