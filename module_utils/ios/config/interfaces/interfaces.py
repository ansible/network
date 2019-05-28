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

from ansible.module_utils.ios.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils.ios.config.base import ConfigBase
from ansible.module_utils.ios.facts.facts import Facts
from ansible.module_utils.ios.utils.utils import get_interface_type, normalize_interface, search_obj_in_list


class Interfaces(ConfigBase, InterfacesArgs):
    """
    The ios_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'interfaces',
    ]

    params = ('description', 'mtu', 'speed', 'duplex')

    def get_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        result = Facts().get_facts(self._module, self._connection, self.gather_subset, self.gather_network_resources)
        facts = result
        interfaces_facts = facts['ansible_network_resources'].get('interfaces')
        if not interfaces_facts:
            return []

        return interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from moduel execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_facts = self.get_interfaces_facts()
        commands.extend(self.set_config(existing_facts))

        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        interfaces_facts = self.get_interfaces_facts()

        result['before'] = existing_facts
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

        for w in want:
            w.update({'name': normalize_interface(w['name'])})
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
            kwargs = {'want': want, 'have': have}
            commands = self._state_overridden(**kwargs)
        elif state == 'deleted':
            kwargs = {'want': want, 'have': have}
            commands = self._state_deleted(**kwargs)
        elif state == 'merged':
            kwargs = {'want': want, 'have': have}
            commands = self._state_merged(**kwargs)
        elif state == 'replaced':
            kwargs = {'want': want, 'have': have}
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

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
                elif interface['name'] in each['name']:
                    break
            else:
                continue
            kwargs = {'want': interface, 'have': each, }
            commands.extend(Interfaces.clear_interface(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands}
            commands.extend(Interfaces.set_interface(**kwargs))

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
                commands.extend(Interfaces.clear_interface(**kwargs))
                continue
            kwargs = {'want': interface, 'have': each}
            commands.extend(Interfaces.clear_interface(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands}
            commands.extend(Interfaces.set_interface(**kwargs))

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

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                continue
            kwargs = {'want': interface, 'have': each}
            commands.extend(Interfaces.set_interface(**kwargs))

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
            commands.extend(Interfaces.clear_interface(**kwargs))

        return commands

    @staticmethod
    def _remove_command_from_interface(interface, cmd, commands):
        # To delete the passed config
        if interface not in commands:
            commands.insert(0, interface)
        commands.append('no %s' % cmd)
        return commands

    @staticmethod
    def _add_command_to_interface(interface, cmd, commands):
        # To set the passed config
        if interface not in commands:
            commands.insert(0, interface)
        commands.append(cmd)

    @staticmethod
    def set_interface(**kwargs):
        # Set the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        clear_cmds = []

        if kwargs.get('commands'):
            clear_cmds = kwargs['commands']

        interface = 'interface ' + want['name']

        if want.get('enabled') and want.get('enabled') != have.get('enabled'):
            Interfaces._add_command_to_interface(interface, 'no shutdown', commands)
        elif not want.get('enabled') and want.get('enabled') != have.get('enabled'):
                Interfaces._add_command_to_interface(interface, 'shutdown', commands)
        for item in Interfaces.params:
            cmd = 'no ' + item
            candidate = want.get(item)
            if candidate and (candidate != have.get(item) or cmd in clear_cmds):
                cmd = item + ' ' + str(candidate)
                Interfaces._add_command_to_interface(interface, cmd, commands)

        return commands

    @staticmethod
    def clear_interface(**kwargs):
        # Delete the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        interface_type = get_interface_type(want['name'])
        interface = 'interface ' + want['name']

        if have.get('description') and want.get('description') != have.get('description'):
            Interfaces._remove_command_from_interface(interface, 'description', commands)
        if not have.get('enabled') and want.get('enabled') != have.get('enabled'):
            # if enable is False set enable as True which is the default behavior
            Interfaces._remove_command_from_interface(interface, 'shutdown', commands)

        if interface_type.lower() == 'gigabitethernet':
            if have.get('speed') and have.get('speed') != 'auto' and want.get('speed') != have.get('speed'):
                Interfaces._remove_command_from_interface(interface, 'speed', commands)
            if have.get('duplex') and have.get('duplex') != 'auto' and want.get('duplex') != have.get('duplex'):
                Interfaces._remove_command_from_interface(interface, 'duplex', commands)
            if have.get('mtu') and want.get('mtu') != have.get('mtu'):
                Interfaces._remove_command_from_interface(interface, 'mtu', commands)

        return commands