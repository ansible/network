#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils


def merge_two_dicts(dict1, dict2):
    dict = dict1.copy()   # start with dict1's keys and values
    dict.update(dict2)    # modifies dict with dict2's keys and values & returns None
    return dict


def search_obj_in_list(name, lst):
    for item in lst:
        for it in item:
            if it == name:
                return item
    return None


def get_member_diff(want_item, have_item):
    if not have_item:
        diff = want_item.get('legacy_protocols') or []
    else:
        want_protocols = want_item.get('legacy_protocols') or []
        have_protocols = have_item.get('legacy_protocols') or []
        diff = list_diff_want_only(want_protocols, have_protocols)
    return diff


def list_diff_have_only(want_list, have_list):
    if have_list and not want_list:
        diff = have_list
    elif not have_list:
        diff = None
    else:
        diff = [i for i in have_list + want_list if i in have_list and i not in want_list]
    return diff


def list_diff_want_only(want_list, have_list):
    if have_list and not want_list:
        diff = None
    elif not have_list:
        diff = want_list
    else:
        diff = [i for i in have_list + want_list if i in want_list and i not in have_list]
    return diff


def add_lldp_protocols(want_item, have_item):
    commands = []
    diff_members = get_member_diff(want_item, have_item)
    for key in diff_members:
        commands.append('set service lldp ' + 'legacy-protocols ' + key)
    return commands


def update_lldp_protocols(want_item, have_item):
    commands = []
    want_protocols = want_item.get('legacy_protocols') or []
    have_protocols = have_item.get('legacy_protocols') or []

    members_diff = list_diff_have_only(want_protocols, have_protocols)
    if members_diff:
        for member in members_diff:
            commands.append('delete service lldp ' + 'legacy-protocols ' + member)
    return commands
