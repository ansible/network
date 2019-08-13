#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The arg spec for the iosxr facts module.
"""

class FactsArgs(object):
    """ The arg spec for the iosxr facts module
    """

    def __init__(self, **kwargs):
        pass

    choices = [
        'all',
        'lacp',
        '!lacp',
        'lacp_interfaces',
        '!lacp_interfaces',
        'lldp_global',
        '!lldp_global',
        'l3_interfaces',
        '!l3_interfaces'
    ]

    argument_spec = {
        'gather_subset': dict(default=['!config'], type='list'),
        'gather_network_resources': dict(default=['all'], choices=choices, type='list'),
    }

