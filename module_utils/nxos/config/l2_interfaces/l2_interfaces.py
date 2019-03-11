#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_l2_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils. \
     nxos.argspec.l2_interfaces.l2_interfaces import L2_interfacesArgs
from ansible.module_utils. \
     nxos. \
     config.base import ConfigBase
from ansible.module_utils. \
     nxos.facts.facts import Facts
from ansible.module_utils.nxos.utils.utils import eliminate_null_keys, normalize_interface, search_obj_in_list, vlan_range_to_list
from ansible.module_utils.six import string_types


class L2_interfaces(ConfigBase, L2_interfacesArgs):
    """
    The nxos_l2_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l2_interfaces',
    ]

    def get_l2_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, warnings = Facts().get_facts(self._module, self._connection, self.gather_subset, self.gather_network_resources)
        l2_interfaces_facts = facts['ansible_network_resources'].get('l2_interfaces')
        if not l2_interfaces_facts:
            return []
        return l2_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_l2_interfaces_facts = self.get_l2_interfaces_facts()
        commands.extend(self.set_config(existing_l2_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
            result['after'] = self.get_l2_interfaces_facts()
        result['commands'] = commands

        result['before'] = existing_l2_interfaces_facts
        result['warnings'] = warnings
        return result

    def set_config(self, existing_l2_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        for w in want:
            w.update({'name': normalize_interface(w['name'])})
            self.expand_trunk_allowed_vlans(w)
        have = existing_l2_interfaces_facts
        for h in have:
            self.expand_trunk_allowed_vlans(h)
        resp = self.set_state(want, have)
        return to_list(resp)

    def expand_trunk_allowed_vlans(self, d):
        if not d:
            return None
        if 'trunk' in d and d['trunk']:
            if 'allowed_vlans' in d['trunk']:
                d['trunk']['allowed_vlans'] = vlan_range_to_list(d['trunk']['allowed_vlans'])

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = list()
        state = self._module.params['state']

        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))
        else:
            for w in want:
                if state in ('merged', 'replaced'):
                    cmd_map = self.generate_cmd_map(w, null=True)
                if state == 'deleted':
                    cmd_map = self.generate_cmd_map(w)
                obj_in_have = search_obj_in_list(w['name'], have)

                if state == 'deleted':
                    commands.extend(self._state_deleted(w, cmd_map, obj_in_have))
                if state == 'merged':
                    commands.extend(self._state_merged(w, cmd_map, obj_in_have))
                if state == 'replaced':
                    commands.extend(self._state_replaced(w, cmd_map, obj_in_have))
        return commands

    def _state_merged(self, w, cmd_map, obj_in_have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        for k, v in cmd_map.items():
            cmd = self.generate_commands(k, v, obj_in_have)
            if cmd:
                commands.append(cmd)
        if commands:
            commands.insert(0, 'interface ' + w['name'])
        return commands

    def _state_deleted(self, w, cmd_map, obj_in_have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if not obj_in_have:
            return commands
        for k, v in cmd_map.items():
            cmd = self.generate_commands(k, v, obj_in_have, delete=True)
            if cmd:
                commands.append(cmd)
        if commands:
            commands.insert(0, 'interface ' + w['name'])
        return commands

    def _state_replaced(self, w, cmd_map, obj_in_have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        merged_commands = self._state_merged(w, cmd_map, obj_in_have)
        if obj_in_have:
            replaced_cmd_map = self.generate_cmd_map(obj_in_have, null=True)
            set_merged = set(cmd_map.items())
            set_replaced = set(replaced_cmd_map.items())
            delta_map = dict(set_merged ^ set_replaced)

            if not delta_map:
                return commands
            for k, v in delta_map.items():
                cmd = self.generate_commands(k, v, obj_in_have, replace=True)
                if cmd:
                    commands.append(cmd)

        if merged_commands:
            cmds = set(commands).intersection(set(merged_commands))
            for cmd in cmds:
                merged_commands.remove(cmd)
            commands.extend(merged_commands)
        else:
            commands.insert(0, 'interface ' + w['name'])
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
            obj_in_want = search_obj_in_list(h['name'], want)
            if not obj_in_want:
                replaced_cmd = []
                hcmd_map = self.generate_cmd_map(h, null=True)
                cmd = []
                if hcmd_map:
                    for k, v in hcmd_map.items():
                        replaced_cmd.append(self.generate_commands(k, v, h, override=True))
                        if replaced_cmd:
                            cmd.extend(replaced_cmd)
                    if cmd:
                        cmd.insert(0, 'interface ' + h['name'])
                    commands.extend(cmd)
            for w in want:
                if w['name'] == h['name']:
                    wcmd_map = self.generate_cmd_map(w, null=True)
                    obj_in_have = search_obj_in_list(w['name'], have)
                    merged_commands.extend(self._state_merged(w, wcmd_map, obj_in_have))
                    if obj_in_want:
                        replaced_cmd = []
                        hcmd_map = self.generate_cmd_map(h, null=True)
                        set_wcmd = set(wcmd_map.items())
                        set_hcmd = set(hcmd_map.items())
                        delta_cmd = dict(set_wcmd ^ set_hcmd)
                        cmd = []
                        if delta_cmd:
                            for k, v in delta_cmd.items():
                                replaced_cmd.append(self.generate_commands(k, v, h, replace=True))
                                if replaced_cmd:
                                    cmd.extend(replaced_cmd)
                        if cmd:
                            cmd.insert(0, 'interface ' + h['name'])
                        commands.extend(cmd)

        if merged_commands:
            commands.extend(merged_commands)

        return commands

    def generate_commands(self, k, v, obj_in_have, delete=False, replace=False, override=False):
        cmd = ''
        conf = 'switchport ' + ' '.join(k.split('_'))

        obj_k = ''
        if obj_in_have:
            access = obj_in_have.get('access', {})
            trunk = obj_in_have.get('trunk', {})

            if k == 'access_vlan' and access:
                obj_k = access.get('vlan')

            if trunk:
                if k == 'trunk_allowed_vlan':
                    obj_k = trunk.get('allowed_vlans')
                if k == 'trunk_native_vlan':
                    obj_k = trunk.get('native_vlan')

        if delete or replace or override:
            conf = 'no ' + conf

        if not obj_in_have and not delete:
            if v and not isinstance(v, list):
                cmd = conf + ' ' + str(v)
            elif v and isinstance(v, list):
                cmd = conf + ' ' + self.list_to_str(v)

        if obj_in_have and not delete:
            if v and v != obj_k and not isinstance(v, list):
                cmd = conf + ' ' + str(v)
            elif v and v != obj_k and isinstance(v, list):
                diff_v = list(set(v) ^ set(obj_k))
                if diff_v:
                    cmd = conf + ' ' + self.list_to_str(diff_v)

        if obj_in_have and delete:
            if obj_k:
                cmd = conf

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

    def list_to_str(self, vlans):
        vlans_list = [str(l) for l in sorted(vlans)]
        res = ",".join(vlans_list)
        return res

    def generate_cmd_map(self, d, null=False):
        if 'access' in d:
            access = d['access'] if d['access'] else {}
        else:
            access = {}
        if 'trunk' in d:
            trunk = d['trunk'] if d['trunk'] else {}
        else:
            trunk = {}

        cmd_map = {
            'access_vlan': access.get('vlan'),
            'trunk_allowed_vlan': trunk.get('allowed_vlans'),
            'trunk_native_vlan': trunk.get('native_vlan'),
        }
        if null:
            return eliminate_null_keys(cmd_map)
        return cmd_map
