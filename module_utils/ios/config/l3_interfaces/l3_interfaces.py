#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_l3_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.six import iteritems

from ansible.module_utils.ios.argspec.l3_interfaces.l3_interfaces import L3_InterfacesArgs
from ansible.module_utils.ios.config.base import ConfigBase
from ansible.module_utils.ios.facts.facts import Facts


class L3_Interfaces(ConfigBase, L3_InterfacesArgs):
    """
    The ios_l3_interfaces class
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
        result = Facts().get_facts(self._module, self._connection, self.gather_subset, self.gather_network_resources)
        facts = result
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
            commands.extend(L3_Interfaces.clear_interface(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands, 'module': module}
            commands.extend(L3_Interfaces.set_interface(**kwargs))

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
                commands.extend(L3_Interfaces.clear_interface(**kwargs))
                continue
            kwargs = {'want': interface, 'have': each}
            commands.extend(L3_Interfaces.clear_interface(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands, 'module': module}
            commands.extend(L3_Interfaces.set_interface(**kwargs))

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
            commands.extend(L3_Interfaces.set_interface(**kwargs))

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
            commands.extend(L3_Interfaces.clear_interface(**kwargs))

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

        return commands

    @staticmethod
    def clear_interface(**kwargs):
        # Delete the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        interface = 'interface ' + want['name']
        if 'ip address' in have:
            L3_Interfaces._remove_command_from_interface(interface, 'no ip address', commands)
        if 'ipv6 address' in have:
            L3_Interfaces._remove_command_from_interface(interface, 'no ipv6 address', commands)

        return commands
    
'library/__init__.py',
'library/ios_facts.py',
'library/ios_l3_interface.py',
'module_utils/__init__.py',
'module_utils/ios/__init__.py',
'module_utils/ios/argspec/__init__.py',
'module_utils/ios/argspec/facts/__init__.py',
'module_utils/ios/argspec/facts/facts.py',
'module_utils/ios/argspec/l3_interfaces/__init__.py',
'module_utils/ios/argspec/l3_interfaces/l3_interfaces.py',
'module_utils/ios/argspec/resource/__init__.py',
'module_utils/ios/argspec/resource/resource.py',
'module_utils/ios/config/__init__.py',
'module_utils/ios/config/base.py',
'module_utils/ios/config/l3_interfaces/__init__.py',
'module_utils/ios/config/l3_interfaces/l3_interfaces.py',
'module_utils/ios/config/resource/__init__.py',
'module_utils/ios/config/resource/resource.py',
'module_utils/ios/facts/__init__.py',
'module_utils/ios/facts/base.py',
'module_utils/ios/facts/facts.py',
'module_utils/ios/facts/l3_interfacs/__init__.py',
'module_utils/ios/facts/l3_interfacs/l3_interfaces.py',
'module_utils/ios/facts/resource/__init__.py',
'module_utils/ios/facts/resource/resource.py',
'module_utils/ios/utils/__init__.py',
'module_utils/ios/utils/utils.py'