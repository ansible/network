#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)


def search_obj_in_list(name, lst, key='name'):
    if lst:
        for item in lst:
            if item[key] == name:
                return item
    return None


def get_interface_type(interface):
    """Gets the type of interface
    """
    if interface.upper().startswith('ET'):
        return 'ethernet'
    elif interface.upper().startswith('BOND'):
        return 'bonding'
    else:
        return 'unknown'
