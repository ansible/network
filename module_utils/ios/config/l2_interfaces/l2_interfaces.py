#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""


from ansible.module_utils.network.common.utils import to_list

from ansible.module_utils.ios.argspec.l2_interfaces.l2_interfaces import L2_InterfacesArgs
from ansible.module_utils.ios.config.base import ConfigBase
from ansible.module_utils.ios.facts.facts import Facts
from ansible.module_utils.ios.utils.utils import get_interface_type, normalize_interface, search_obj_in_list


class L2_Interfaces(ConfigBase, L2_InterfacesArgs):
    """
    The ios_l2_interfaces class
    """

    gather_subset = [
        'net_configuration_interfaces',
    ]

    params = ('access', 'trunk')
    access_cmds = {'access_vlan': 'switchport access vlan'}
    trunk_cmds = {'encapsulation': 'switchport trunk encapsulation', 'pruning_vlans': 'switchport trunk pruning vlan',
                  'native_vlan': 'switchport trunk native vlan', 'allowed_vlans': 'switchport trunk allowed vlan'}

    def get_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)
        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts = Facts().get_facts(self._module, self._connection, self.gather_subset)
        interfaces_facts = facts['net_configuration'].get('interfaces')
        if not interfaces_facts:
            return []
        return interfaces_facts

    def execute_module(self):
        """ Execute the module
        :rtype: A dictionary
        :returns: The result from moduel execution
        """
        result = {'changed': False}
        commands = []
        warnings = []
        existing_facts = self.get_interfaces_facts()
        commands.extend(self.set_config(existing_facts))
        result['before'] = existing_facts
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        interfaces_facts = self.get_interfaces_facts()

        if result['changed']:
            result['after'] = interfaces_facts
        result['warnings'] = warnings
        return result

    def set_config(self, existing_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """

        want = self._module.params['config']
        have = existing_facts
        resp = self.set_state(want, have)

        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided
        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = []

        state = self._module.params['state']
        if state == 'overridden':
            kwargs = {'want': want, 'have': have, 'module': self._module}
            commands = self._state_overridden(**kwargs)
        elif state == 'deleted':
            kwargs = {'want': want, 'have': have, 'module': self._module}
            commands = self._state_deleted(**kwargs)
        elif state == 'merged':
            kwargs = {'want': want, 'have': have, 'module': self._module}
            commands = self._state_merged(**kwargs)
        elif state == 'replaced':
            kwargs = {'want': want, 'have': have, 'module': self._module}
            commands = self._state_replaced(**kwargs)

        return commands

    @staticmethod
    def _state_replaced(**kwargs):
        """ The command generator when state is replaced
        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :param interface_type: interface type
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        module = kwargs['module']

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                continue
            kwargs = {'want': interface, 'have': each,}
            commands.extend(L2_Interfaces.clear_interface(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands, 'module': module}
            commands.extend(L2_Interfaces.set_interface(**kwargs))

        return commands

    @staticmethod
    def _state_overridden(**kwargs):
        """ The command generator when state is overridden
        :param want: the desired configuration as a dictionary
        :param obj_in_have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        module = kwargs['module']

        for each in have:
            for interface in want:
                if each['name'] == interface['name']:
                    break
            else:
                # We didn't find a matching desired state, which means we can
                # pretend we recieved an empty desired state.
                interface = dict(name=each['name'])
                kwargs = {'want': interface, 'have': each}
                commands.extend(L2_Interfaces.clear_interface(**kwargs))
                continue
            kwargs = {'want': interface, 'have': each}
            commands.extend(L2_Interfaces.clear_interface(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands, 'module': module}
            commands.extend(L2_Interfaces.set_interface(**kwargs))

        return commands

    @staticmethod
    def _state_merged(**kwargs):
        """ The command generator when state is merged
        :param want: the additive configuration as a dictionary
        :param obj_in_have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        module = kwargs['module']

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                continue
            kwargs = {'want': interface, 'have': each, 'module': module}
            commands.extend(L2_Interfaces.set_interface(**kwargs))

        return commands

    @staticmethod
    def _state_deleted(**kwargs):
        """ The command generator when state is deleted
        :param want: the objects from which the configuration should be removed
        :param obj_in_have: the current configuration as a dictionary
        :param interface_type: interface type
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        want = kwargs['want']
        have = kwargs['have']

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                continue
            interface = dict(name=interface['name'])
            kwargs = {'want': interface, 'have': each}
            commands.extend(L2_Interfaces.clear_interface(**kwargs))

        return commands

    @staticmethod
    def _remove_command_from_interface(interface, cmd, commands):
        if interface not in commands:
            commands.insert(0, interface)
        if 'no switchport mode' not in commands:
            commands.insert(1, 'no switchport mode')
        commands.append('no %s' % cmd)
        return commands

    @staticmethod
    def _add_command_to_interface(interface, cmd, commands):
        if interface not in commands:
            commands.insert(0, interface)
        commands.append(cmd)

    @staticmethod
    def set_interface(**kwargs):
        # Set the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        module = kwargs['module']
        clear_cmds = []
        if kwargs.get('commands'):
            clear_cmds = kwargs['commands']

        interface = 'interface ' + want['name']
        wants_access = want["access"]
        if wants_access:
            access_vlan = wants_access[0].get("vlan")
            if access_vlan and access_vlan != have.get("access", {}).get("vlan") or\
                    'no switchport access vlan' in clear_cmds:
                cmd = L2_Interfaces.access_cmds['access_vlan'] + ' {}'.format(access_vlan)
                L2_Interfaces._add_command_to_interface(interface, 'switchport mode access', commands)
                L2_Interfaces._add_command_to_interface(interface, cmd, commands)

        wants_trunk = want["trunk"]
        if wants_trunk:
            has_trunk = have.get("trunk", {})
            encapsulation = wants_trunk[0].get("encapsulation")
            if not encapsulation and not has_trunk.get("encapsulation"):
                module.fail_json(msg='Switchport Trunk mode cannot be configured with negotiate encapsulation!')
            if encapsulation and (encapsulation != has_trunk.get("encapsulation") or\
                    'no switchport trunk encapsulation' in clear_cmds):
                cmd = L2_Interfaces.trunk_cmds['encapsulation'] + ' {}'.format(encapsulation)
                L2_Interfaces._add_command_to_interface(interface, cmd, commands)

            if commands and 'switchport mode trunk' not in commands or 'no switchport mode' in clear_cmds:
                L2_Interfaces._add_command_to_interface(interface, 'switchport mode trunk', commands)

            native_vlan = wants_trunk[0].get("native_vlan")
            if native_vlan and (native_vlan != has_trunk.get("native_vlan") or\
                    'no switchport trunk native vlan' in clear_cmds):
                cmd = L2_Interfaces.trunk_cmds['native_vlan'] + ' {}'.format(native_vlan)
                L2_Interfaces._add_command_to_interface(interface, cmd, commands)

            allowed_vlans = wants_trunk[0].get("allowed_vlans")
            has_allowed = has_trunk.get("allowed_vlans")
            if allowed_vlans:
                allowed_vlans = (",".join(map(str, allowed_vlans)))
            if allowed_vlans and (allowed_vlans != has_allowed or 'no switchport trunk allowed vlan' in clear_cmds):
                cmd = L2_Interfaces.trunk_cmds['allowed_vlans'] + ' {}'.format(allowed_vlans)
                L2_Interfaces._add_command_to_interface(interface, cmd, commands)

            pruning_vlans = wants_trunk[0].get("pruning_vlans")
            has_pruning = has_trunk.get("pruning_vlans")
            if pruning_vlans:
                pruning_vlans = (",".join(map(str, pruning_vlans)))

            if pruning_vlans and (pruning_vlans != has_pruning or 'no switchport trunk pruning vlan' in clear_cmds):
                cmd = L2_Interfaces.trunk_cmds['pruning_vlans'] + ' {}'.format(pruning_vlans)
                L2_Interfaces._add_command_to_interface(interface, cmd, commands)

        return commands

    @staticmethod
    def clear_interface(**kwargs):
        # Delete the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        interface = 'interface ' + want['name']

        if "access" in have and not want.get('access'):
            L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.access_cmds['access_vlan'], commands)

        has_trunk = have.get("trunk") or {}
        wants_trunk = want.get("trunk") or {}
        if wants_trunk:
            wants_trunk = wants_trunk[0]
        if "encapsulation" in has_trunk and "encapsulation" not in wants_trunk:
            L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.trunk_cmds['encapsulation'], commands)
        if "allowed_vlans" in has_trunk and "allowed_vlans" not in wants_trunk:
            L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.trunk_cmds['allowed_vlans'], commands)
        if "native_vlan" in has_trunk and "native_vlan" not in wants_trunk:
            L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.trunk_cmds['native_vlan'], commands)
        if "pruning_vlans" in has_trunk and "pruning_vlans" not in wants_trunk:
            L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.trunk_cmds['pruning_vlans'], commands)

        return commands
