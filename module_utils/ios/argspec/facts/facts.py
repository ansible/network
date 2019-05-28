#!/usr/bin/python
# -*- coding: utf-8 -*-
# {{ rm['COPYRIGHT'] }}
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The arg spec for the iosxr facts module.
"""

class FactsArgs(object): #pylint: disable=R0903
    """ The arg spec for the ios facts module
    """
    def __init__(self, **kwargs):
        pass

    choices = [
        'all',
        'interfaces',
    ]
    argument_spec = {
        'gather_subset': dict(default=['!config'], type='list'),
        'gather_network_resources': dict(default=['all'], choices=choices, type='list'),
    }
