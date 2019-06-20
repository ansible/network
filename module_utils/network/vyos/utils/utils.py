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

def get_arp_monitor_diff(want_item, have_item):
    want_arp_target = []
    have_arp_target = []
    want_arp_monitor = want_item.get('arp-monitor') or {}
    have_arp_monitor = have_item.get('arp-monitor') or {}

    if want_arp_monitor and 'target' in want_arp_monitor:
        want_arp_target = want_arp_monitor['target']

    if have_arp_monitor and 'target' in have_arp_monitor:
        have_arp_target = have_arp_monitor['target']

    diff = list_diff_for_update(have_arp_target, want_arp_target)
    return diff

def get_member_diff(want_item, have_item):
    want_members = want_item.get('members') or []
    have_members = have_item.get('members') or []
    diff = list_diff_for_update(have_members, want_members)
    return diff

def list_diff_have(have_list, want_list):
    if have_list and not want_list:
        diff = have_list
    elif not have_list:
        diff = None
    else:
        diff = [i for i in have_list + want_list if i in have_list and  i not in want_list]
    return diff

def list_diff_for_update(have_list, want_list):
    if have_list and not want_list:
        diff = None
    elif not have_list:
        diff = want_list
    else:
        diff = [i for i in have_list + want_list if i in want_list and  i not in have_list]
    return diff
