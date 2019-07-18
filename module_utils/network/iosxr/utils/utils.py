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


def list_to_dict(param_list, key='name'):
    param_dict = {}

    if param_list:
        for params in param_list:
            name = params.pop(key)
            param_dict[name] = params

    return param_dict


def diff_list_of_dicts(w, h):
    if not w:
        w = []
    if not h:
        h = []
    diff = []
    set_w = set(tuple(d.items()) for d in w)
    set_h = set(tuple(d.items()) for d in h)
    difference = set_w.difference(set_h)
    for element in difference:
        diff.append(dict((x, y) for x, y in element))
    return diff
