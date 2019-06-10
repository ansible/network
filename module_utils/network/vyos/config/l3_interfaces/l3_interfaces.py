#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_l3_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.network.common.utils import to_list

from ansible.module_utils.network. \
    vyos.argspec.l3_interfaces.l3_interfaces import L3_interfacesArgs
from ansible.module_utils.network. \
    vyos. \
    config.base import ConfigBase
from ansible.module_utils.network. \
    vyos.facts.facts import Facts
from ansible.module_utils.network. \
    vyos.utils.utils import search_obj_in_list, get_interface_type
from ansible.module_utils.six import iteritems


class L3_interfaces(ConfigBase, L3_interfacesArgs):
    """
    The vyos_l3_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l3_interfaces',
    ]

    set_cmd = 'set interfaces '
    del_cmd = 'delete interfaces '

    def get_l3_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts().get_facts(self._module,
                                             self._connection,
                                             self.gather_subset,
                                             self.gather_network_resources)
        l3_interfaces_facts = facts['ansible_network_resources'].get('l3_interfaces')
        if not l3_interfaces_facts:
            return []
        return l3_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_l3_interfaces_facts = self.get_l3_interfaces_facts()
        commands.extend(self.set_config(existing_l3_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_l3_interfaces_facts = self.get_l3_interfaces_facts()

        result['before'] = existing_l3_interfaces_facts
        if result['changed']:
            result['after'] = changed_l3_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l3_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_l3_interfaces_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want=want, have=have)
        else:
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have)

                if state == 'deleted':
                    commands.extend(
                        L3_interfaces._state_deleted(have_intf=obj_in_have)
                    )
                elif state == 'merged':
                    commands.extend(
                        L3_interfaces._state_merged(
                            want_intf=item, have_intf=obj_in_have)
                    )
                elif state == 'replaced':
                    commands.extend(
                        L3_interfaces._state_replaced(
                            want_intf=item, have_intf=obj_in_have)
                    )
        return commands

    @staticmethod
    def _state_replaced(**kwargs):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want_intf = kwargs['want_intf']
        have_intf = kwargs['have_intf']

        if have_intf:
            commands.extend(
                L3_interfaces._render_del_commands(
                    want_element={
                        'intf': want_intf
                    },
                    have_element={
                        'intf': have_intf
                    }
                )
            )

            have_vifs = have_intf.get('vifs')
            want_vifs = want_intf['vifs']

            if have_vifs:
                for have_vif in have_vifs:
                    want_vif = {}
                    want_vif = search_obj_in_list(
                        have_vif['vlan_id'], want_vifs, key='vlan_id'
                    )
                    if not want_vif:
                        want_vif = {}

                    commands.extend(
                        L3_interfaces._render_del_commands(
                            want_element={
                                'intf': want_intf,
                                'vif': want_vif
                            },
                            have_element={
                                'intf': have_intf,
                                'vif': have_vif
                            }
                        )
                    )

        commands.extend(
            L3_interfaces._state_merged(
                want_intf=want_intf,
                have_intf=have_intf
            )
        )

        return commands

    @staticmethod
    def _state_overridden(**kwargs):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want_intfs = kwargs['want']
        have_intfs = kwargs['have']

        for have_intf in have_intfs:
            intf_name = have_intf['name']
            intf_in_want = search_obj_in_list(intf_name, want_intfs)
            if not intf_in_want:
                commands.extend(
                    L3_interfaces._state_deleted(
                        have_intf=have_intf))

        for intf in want_intfs:
            name = intf['name']
            intf_in_have = search_obj_in_list(name, have_intfs)
            commands.extend(
                L3_interfaces._state_replaced(
                    want_intf=intf,
                    have_intf=intf_in_have)
            )

        return commands

    @staticmethod
    def _state_merged(**kwargs):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        want_intf = kwargs['want_intf']
        have_intf = kwargs['have_intf']

        if have_intf:
            commands.extend(
                L3_interfaces._render_updates(
                    want_element={'intf': want_intf},
                    have_element={'intf': have_intf}
                )
            )

            have_vifs = have_intf.get('vifs')
            want_vifs = want_intf['vifs']

            if want_vifs:
                for want_vif in want_vifs:
                    have_vif = {}
                    have_vif = search_obj_in_list(
                        want_vif['vlan_id'], have_vifs, key='vlan_id'
                    )
                    if not have_vif:
                        have_vif = {}

                    if have_vif:
                        commands.extend(
                            L3_interfaces._render_updates(
                                want_element={
                                    'intf': want_intf,
                                    'vif': want_vif
                                },
                                have_element={
                                    'intf': have_intf,
                                    'vif': have_vif
                                }
                            )
                        )

                    else:
                        commands.extend(
                            L3_interfaces._render_set_commands(
                                want_element={
                                    'intf': want_intf,
                                    'vif': want_vif
                                }
                            )
                        )
        else:
            commands.extend(
                L3_interfaces._render_set_commands(
                    want_element={
                        'intf': want_intf,
                    }
                )
            )

        return commands

    @staticmethod
    def _state_deleted(**kwargs):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        have_intf = kwargs['have_intf']
        have_intf_name = have_intf['name']

        if have_intf:
            if (have_intf.get('ipv4') or have_intf.get('ipv6')):
                interface = get_interface_type(have_intf_name) + ' ' + have_intf_name
                commands.append(
                    L3_interfaces.del_cmd + interface + ' address'
                )

            have_intf_vifs = have_intf.get('vifs')

            if have_intf_vifs:
                for vif in have_intf_vifs:
                    if (vif.get('ipv4') or vif.get('ipv6')):
                        interface = get_interface_type(have_intf_name) + ' ' + have_intf_name
                        commands.append(
                            L3_interfaces.del_cmd + interface + ' vif ' + vif['vlan_id'] + ' address'
                        )

        return commands

    @staticmethod
    def _render_updates(**kwargs):
        commands = []
        want_element = kwargs['want_element']
        have_element = kwargs['have_element']

        intf_name = have_element['intf']['name']

        if have_element.get('vif'):
            set_cmd = L3_interfaces.set_cmd + get_interface_type(intf_name) + \
                ' ' + intf_name + ' vif ' + have_element['vif']['vlan_id']
            have_item = have_element['vif']
            want_item = want_element['vif']
        else:
            set_cmd = L3_interfaces.set_cmd + get_interface_type(intf_name) + ' ' + intf_name
            have_item = have_element['intf']
            want_item = want_element['intf']

        for key, value in iteritems(want_item):
            if key in ['ipv4', 'ipv6'] and value:
                for item in value:
                    have_ipaddrs = have_item.get(key)
                    if (not have_ipaddrs) or (
                            have_ipaddrs and item not in have_ipaddrs):
                        commands.append(set_cmd + ' address \'' + item['address'] + "'")

        return commands

    @staticmethod
    def _render_set_commands(**kwargs):
        commands = []
        want_element = kwargs['want_element']
        intf_name = want_element['intf']['name']
        set_cmd = L3_interfaces.set_cmd + get_interface_type(intf_name) + ' ' + intf_name

        if want_element.get('vif'):
            set_cmd = set_cmd + ' vif ' + want_element['vif']['vlan_id']
            want_item = want_element['vif']

        else:
            want_item = want_element['intf']

        for attrib in ['ipv4', 'ipv6']:
            value = want_item[attrib]
            if value:
                for item in value:
                    commands.append(set_cmd + ' address \'' + item['address'] + "'")

        return commands

    @staticmethod
    def _render_del_commands(**kwargs):
        commands = []
        want_element = kwargs['want_element']
        have_element = kwargs['have_element']
        intf_name = have_element['intf']['name']
        del_cmd = L3_interfaces.del_cmd + get_interface_type(intf_name) + ' ' + intf_name

        if have_element.get('vif'):
            del_cmd = del_cmd + ' vif ' + \
                have_element['vif']['vlan_id'].strip("'")
            have_item = have_element['vif']
            want_item = want_element['vif']
        else:
            have_item = have_element['intf']
            want_item = want_element['intf']

        for attrib in ['ipv4', 'ipv6']:
            want_addr = None
            if want_item:
                want_addr = want_item.get(attrib)
            if not want_addr:
                want_addr = []
            have_addr = have_item.get(attrib)

            if have_addr:
                for item in have_addr:
                    if item not in want_addr:
                        commands.append(del_cmd + ' address \'' + item['address'] + "'")

        return commands
