#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils


def search_obj_in_list(name, lst, key='name'):
    for item in lst:
        if item[key] == name:
            return item
    return None


def get_interface_type(interface):
    """Gets the type of interface
    """
    if interface.startswith('eth'):
        return 'ethernet'
    elif interface.startswith('bond'):
        return 'bonding'
    elif interface.startswith('vti'):
        return 'vti'
    elif interface.startswith('lo'):
        return 'loopback'
