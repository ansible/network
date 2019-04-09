#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The arg spec for the ios facts module.
"""

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

