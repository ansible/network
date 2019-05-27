#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_l2_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.six import iteritems

from ansible.module_utils.iosxr.argspec.l2_interfaces.l2_interfaces import L2_InterfacesArgs
from ansible.module_utils.iosxr.config.base import ConfigBase
from ansible.module_utils.iosxr.facts.facts import Facts


class L2_Interfaces(ConfigBase, L2_InterfacesArgs):
    """
    The iosxr_l2_interfaces class
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
        result = Facts().get_facts(self._module, self._connection, self.gather_subset, self.gather_network_resources)
        facts = result
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
        result['commands'] = commands

        changed_l2_interfaces_facts = self.get_l2_interfaces_facts()

        result['before'] = existing_l2_interfaces_facts
        if result['changed']:
            result['after'] = changed_l2_interfaces_facts

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
        have = existing_l2_interfaces_facts
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

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        module = kwargs['module']

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
                elif interface['name'] in each['name']:
                    break
            else:
                continue
            kwargs = {'want': interface, 'have': each, }
            commands.extend(L2_Interfaces.clear_interface(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands, 'module': module}
            commands.extend(L2_Interfaces.set_interface(**kwargs))

        return commands

    @staticmethod
    def _state_overridden(**kwargs):
        """ The command generator when state is overridden

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
                elif interface['name'] in each['name']:
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
                elif interface['name'] in each['name']:
                    break
            else:
                continue
            kwargs = {'want': interface, 'have': each, 'module': module}
            commands.extend(L2_Interfaces.set_interface(**kwargs))

        return commands

    @staticmethod
    def _state_deleted(**kwargs):
        """ The command generator when state is deleted

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
                elif interface['name'] in each['name']:
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
        wants_native = want["native_vlan"]
        if wants_native and wants_native != str(have.get("native_vlan", {}).get("vlan")) or\
            'no dot1q native vlan' in clear_cmds:
            cmd = 'dot1q native vlan {}'.format(wants_native)
            L2_Interfaces._add_command_to_interface(interface, cmd, commands)

        if want.get('l2transport'):
            if want.get('l2protocol'):
                for each in want.get('l2protocol'):
                    for k, v in iteritems(each):
                        l2ptotocol_type = 'l2protocol_' + k
                        if have.get(l2ptotocol_type) != v:
                            cmd = 'l2transport l2protocol ' + k + ' ' + v
                            L2_Interfaces._add_command_to_interface(interface, cmd, commands)
            if want.get('propagate') and not have.get('propagate'):
                cmd = 'l2transport propagate remote-status'
                L2_Interfaces._add_command_to_interface(interface, cmd, commands)
        elif want.get('l2protocol') or want.get('propagate'):
            module.fail_json(msg='L2transports L2protocol or Propagate can only be configured when'
                                 'L2transprt set to True!')

        if want.get('q_vlan'):
            q_vlans = (" ".join(map(str, want.get('q_vlan'))))
            if q_vlans != have.get('q_vlan'):
                if 'any' in q_vlans and 'l2transport' in interface:
                    cmd = 'dot1q vlan {}'.format(q_vlans)
                    L2_Interfaces._add_command_to_interface(interface, cmd, commands)
                else:
                    cmd = 'dot1q vlan {}'.format(q_vlans)
                    L2_Interfaces._add_command_to_interface(interface, cmd, commands)

        return commands

    @staticmethod
    def clear_interface(**kwargs):
        # Delete the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        interface = 'interface ' + want['name']

        if 'q_vlan' in have and 'l2transport' in have['name'] and want['name'] in have['name']:
            L2_Interfaces._remove_command_from_interface(interface, 'dot1q vlan', commands)
        elif 'q_vlan' in have and 'l2transport' not in have['name'] and want['name'] in have['name']:
            L2_Interfaces._remove_command_from_interface(interface, 'encapsulation dot1q', commands)

        if 'native_vlan' in have and want.get('native_vlan') != str(have.get('native_vlan').get('vlan')):
            L2_Interfaces._remove_command_from_interface(interface, 'dot1q native vlan', commands)
        if want.get('l2transport'):
            if want.get('l2protocol'):
                for each in want.get('l2protocol'):
                    for k, v in iteritems(each):
                        l2ptotocol_type = 'l2protocol_' + k
                        if have.get(l2ptotocol_type) != v:
                            L2_Interfaces._remove_command_from_interface(interface, 'l2transport', commands)
        if have.get('l2transport') and not want.get('l2transport'):
            if 'no l2transport' not in commands:
                L2_Interfaces._remove_command_from_interface(interface, 'l2transport', commands)

        return commands