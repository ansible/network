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


def get_arp_monitor_target_diff(want_item, have_item):
    want_arp_target = []
    have_arp_target = []

    want_arp_monitor = want_item.get('arp-monitor') or {}
    if want_arp_monitor and 'target' in want_arp_monitor:
        want_arp_target = want_arp_monitor['target']

    if not have_item:
        diff = want_arp_target
    else:
        have_arp_monitor = have_item.get('arp-monitor') or {}
        if have_arp_monitor and 'target' in have_arp_monitor:
            have_arp_target = have_arp_monitor['target']

        diff = list_diff_want_only(want_arp_target, have_arp_target)
    return diff


def get_member_diff(want_item, have_item):
    if not have_item:
        diff = want_item.get('members') or []
    else:
        want_members = want_item.get('members') or []
        have_members = have_item.get('members') or []
        diff = list_diff_want_only(want_members, have_members)
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


def add_bond_members(want_item, have_item):
    commands = []
    bond_name = want_item['name']
    diff_members = get_member_diff(want_item, have_item)
    if diff_members:
        for m in diff_members:
            commands.append(
                'set interfaces ethernet ' + m + ' bond-group ' + bond_name
            )
    return commands


def add_arp_monitor(updates, set_cmd, key, want_item, have_item):
    commands = []
    arp_monitor = updates.get('arp-monitor') or {}
    diff_targets = get_arp_monitor_target_diff(want_item, have_item)

    if 'interval' in arp_monitor:
        commands.append(
            set_cmd + ' ' + key + ' interval ' + str(arp_monitor['interval'])
        )
    if diff_targets:
        for target in diff_targets:
            commands.append(
                set_cmd + ' ' + key + ' target ' + target
            )
    return commands


def delete_arp_monitor(del_lag, delete_arp_monitor):
    commands = []
    if 'interval' in delete_arp_monitor:
        commands.append(
            del_lag + ' ' + 'arp-monitor' + ' interval'
        )
    if 'target' in delete_arp_monitor:
        for target in delete_arp_monitor['target']:
            commands.append(
                del_lag + ' ' + 'arp-monitor' + ' target ' + target
            )
    return commands


def delete_bond_members(lag):
    commands = []
    for member in lag['members']:
        commands.append(
            'delete interfaces ethernet ' + member + ' bond-group ' + lag['name']
        )
    return commands


def update_arp_monitor(del_cmd, want_item, have_item):
    commands = []
    want_arp_target = []
    have_arp_target = []
    want_arp_monitor = want_item.get('arp-monitor') or {}
    have_arp_monitor = have_item.get('arp-monitor') or {}

    if want_arp_monitor and 'target' in want_arp_monitor:
        want_arp_target = want_arp_monitor['target']

    if have_arp_monitor and 'target' in have_arp_monitor:
        have_arp_target = have_arp_monitor['target']

    if 'interval' in have_arp_monitor and not want_arp_monitor:
        commands.append(del_cmd + ' ' + 'arp-monitor' + ' interval')
    if 'target' in have_arp_monitor:
        target_diff = list_diff_have_only(want_arp_target, have_arp_target)
        if target_diff:
            for target in target_diff:
                commands.append(del_cmd + ' ' + 'arp-monitor' + ' target ' + target)

    return commands


def update_bond_members(want_item, have_item):
    commands = []
    name = have_item['name']
    want_members = want_item.get('members') or []
    have_members = have_item.get('members') or []

    members_diff = list_diff_have_only(want_members, have_members)
    if members_diff:
        for member in members_diff:
            commands.append('delete interfaces ethernet ' + member + ' bond-group ' + name)
    return commands
