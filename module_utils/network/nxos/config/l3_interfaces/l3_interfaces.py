#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_l3_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.six import iteritems

from ansible.module_utils.network. \
    nxos.argspec.l3_interfaces.l3_interfaces import L3_interfacesArgs
from ansible.module_utils.network. \
    nxos. \
    config.base import ConfigBase
from ansible.module_utils.network. \
    nxos.facts.facts import Facts
from ansible.module_utils.network. \
    nxos.utils.utils import eliminate_null_keys, \
    normalize_interface, search_obj_in_list

class L3_interfaces(ConfigBase, L3_interfacesArgs):
    """
    The nxos_l3_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l3_interfaces',
    ]

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
        for w in want:
            w.update({'name': normalize_interface(w['name'])})
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
        state = self._module.params['state']
        commands = list()

        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))
        else:
            for w in want:
                obj_in_have = search_obj_in_list(w['name'], have)
                if state in ('merged', 'replaced'):
                    cmd_map = self.generate_cmd_map(w, null=True)
                    if state == 'merged':
                        commands.extend(self._state_merged(w, cmd_map, obj_in_have))
                    elif state == 'replaced':
                        commands.extend(self._state_replaced(w, cmd_map, obj_in_have))
                elif state == 'deleted':
                    commands.extend(self._state_deleted(w['name'], obj_in_have))
        return commands

    def _state_replaced(self, w, cmd_map, obj_in_have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        merged_commands = self._state_merged(w, cmd_map, obj_in_have)
        replaced_commands = self._state_deleted(w['name'], obj_in_have)
        if merged_commands:
            cmds = set(replaced_commands).intersection(set(merged_commands))
            for cmd in cmds:
                merged_commands.remove(cmd)
            commands.extend(replaced_commands)
            commands.extend(merged_commands)
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        merged_commands = []
        for h in have:
            obj_in_want = eliminate_null_keys(search_obj_in_list(h['name'], want))
            if not obj_in_want:
                commands.extend(self._state_deleted(h['name'], h))
            for w in want:
                if w['name'] == h['name']:
                    wcmd_map = self.generate_cmd_map(w, null=True)
                    obj_in_have = search_obj_in_list(w['name'], have)
                    hcmd_map = self.generate_cmd_map(h, null=True)
                    if wcmd_map != hcmd_map:
                        commands.extend(self._state_deleted(w['name'], obj_in_have))
                        merged_commands = self._state_merged(w, wcmd_map, obj_in_have)
                elif w['name'] != h['name']:
                    wcmd_map = self.generate_cmd_map(w, null=True)
                    obj_in_have = search_obj_in_list(w['name'], have)
                    merged_commands = self._state_merged(w, wcmd_map, obj_in_have)
        if merged_commands:
            commands.extend(merged_commands)

        return commands

    def _state_merged(self, w, cmd_map, obj_in_have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for item in cmd_map:
            cmd = self.generate_commands(item, obj_in_have)
            if cmd:
                commands.append(cmd)
        if commands:
            commands.insert(0, 'interface ' + w['name'])
        return commands

    def _state_deleted(self, name, obj_in_have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if obj_in_have:
            if 'ipv4' in obj_in_have:
                commands.append('no ip address')
            if 'ipv6' in obj_in_have:
                commands.append('no ipv6 address')
        if commands:
            commands.insert(0, 'interface ' + name)
        return commands

    def generate_commands(self, item, obj_in_have, replace=False, override=False):
        cmd = ''
        conf = ''
        addr_type = item['addr_type']
        del item['addr_type']

        if replace or override:
            conf = 'no ' + addr_type + ' address'
        else:
            conf = addr_type + ' address'

        obj_k = []
        if obj_in_have:
            if addr_type == 'ip':
                obj_k = obj_in_have.get('ipv4')
            else:
                obj_k = obj_in_have.get(addr_type)

        if not obj_in_have:
            cmd = conf + ' ' + item['address']
            cmd = self.add_command_to_interface(item, cmd)

        if obj_in_have:
            existing_addresses = []
            for obj in obj_k:
                existing_addresses.append(obj['address'])
                if obj['address'] == item['address']:
                    set_obj = set(obj.items())
                    set_item = set(item.items())
                    delta = dict(set_item - set_obj)
                    if delta:
                        cmd = conf + ' ' + item['address']
                        cmd = self.add_command_to_interface(delta, cmd)
            if item['address'] not in existing_addresses:
                cmd = conf + ' ' + item['address']
                cmd = self.add_command_to_interface(item, cmd)

        if obj_in_have and replace:
            if obj_k:
                cmd = conf

        if override:
            if access:
                if 'vlan' in obj_in_have['access']:
                    cmd = conf
            elif trunk:
                if 'allowed_vlans' in obj_in_have['trunk'] or 'native_vlan' in obj_in_have['trunk']:
                    cmd = conf
        return cmd

    def add_command_to_interface(self, delta, cmd):
        if 'secondary' in delta:
            if delta['secondary'] == True:
                cmd = cmd + ' ' + 'secondary'
            if delta['secondary'] == False:
                cmd = 'no' + ' ' + cmd + ' ' + 'secondary'
            if 'tag' in delta:
                cmd = cmd + ' ' + 'tag' + ' ' + str(delta['tag'])
        elif 'tag' in delta:
            cmd = cmd + ' ' + 'tag' + ' ' + str(delta['tag'])
        return cmd

    def item_map(self, val, prefix):
        c_map = {}
        if not val:
            return c_map

        address = val['address']
        if 'secondary' in val:
            secondary = val['secondary'] if val['secondary'] else None
        else:
            secondary = None
        if 'tag' in val:
            tag = val['tag'] if val['tag'] else None
        else:
            tag = None

        if prefix == 'ip':
            c_map = {
                'address': address,
                'secondary': secondary,
                'tag': tag,
                'addr_type': 'ip',
            }
        else:
            c_map = {
                'address': address,
                'secondary': secondary,
                'tag': tag,
                'addr_type': 'ipv6',
            }
        return c_map

    def generate_cmd_map(self, d, null=False):
        cmd_map = []
        ipv4_list = []
        ipv6_list = []

        for key, val in iteritems(d):
            if key == 'ipv4':
                if val:
                    for v in val:
                        c_map = self.item_map(v, prefix='ip')
                        if c_map:
                            ipv4_list.append(c_map)
            if key == 'ipv6':
                if val:
                    for v in val:
                        c_map = self.item_map(v, prefix='ipv6')
                        if c_map:
                            ipv6_list.append(c_map)

        for i in (ipv4_list, ipv6_list):
            if i:
                cmd_map.extend(i)
        if null:
            return eliminate_null_keys(cmd_map)
        return cmd_map
