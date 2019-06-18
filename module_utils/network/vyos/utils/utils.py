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

def member_list_diff(have_member, want_member):
    if have_member and not want_member:
        diff = have_member
    elif not have_member:
        diff = None
    else:
        diff = [i for i in have_member + want_member if i in have_member and  i not in want_member]
    return diff

def member_list_diff_update(have_member, want_member):
    if have_member and not want_member:
        diff = None
    elif not have_member:
        diff = want_member
    else:
        diff = [i for i in have_member + want_member if i in want_member and  i not in have_member]
    return diff


