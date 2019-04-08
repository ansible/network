#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.network.common.utils import to_list

from ansible.module_utils.eos.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils.eos.config.base import ConfigBase
from ansible.module_utils.eos.facts.facts import Facts


class Interfaces(ConfigBase, InterfacesArgs):
    """
    The eos_interfaces class
    """

    gather_subset = [
        'net_configuration_interfaces',
    ]

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
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_interfaces_facts = self.get_interfaces_facts()
        commands.extend(self.set_config(existing_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_interfaces_facts = self.get_interfaces_facts()

        result['before'] = existing_interfaces_facts
        if result['changed']:
            result['after'] = changed_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_interfaces_facts
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
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)
        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        replace, remove = _param_diff(want, have, replace=True, remove=True)

        commands_by_interface = _replace_config(replace)
        remove_by_interface = _remove_config(remove)
        for interface, commands in remove_by_interface.items():
            current_commands = commands_by_interface.get(interface, [])
            current_commands.extend(commands)
            commands_by_interface[interface] = current_commands

        commands = []
        for interface, interface_commands in commands_by_interface.items():
            commands.append('interface {}'.format(interface))
            commands.extend(interface_commands)

        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        replace = {}
        remove = {}
        for extant in have:
            key = extant['name']
            for config in want:
                if config['name'] == key:
                    break
            else:
                config = {}

            replace[key] = dict(set(config.items()).difference(extant.items()))
            remove[key] = dict(
                (k, v) for k, v in set(extant.items()).difference(config.items())
                if k not in replace[key]
            )

        commands_by_interface = _replace_config(replace)
        remove_by_interface = _remove_config(remove)
        for interface, commands in remove_by_interface.items():
            current_commands = commands_by_interface.get(interface, [])
            current_commands.extend(commands)
            commands_by_interface[interface] = current_commands

        commands = []
        for interface, interface_commands in commands_by_interface.items():
            commands.append('interface {}'.format(interface))
            commands.extend(interface_commands)

        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        replace, = _param_diff(want, have, replace=True)

        commands_by_interface = _replace_config(replace)

        commands = []
        for interface, interface_commands in commands_by_interface.items():
            commands.append('interface {}'.format(interface))
            commands.extend(interface_commands)

        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        remove, = _param_diff(want, have, remove=True)

        commands_by_interface = _remove_config(remove)

        commands = []
        for interface, interface_commands in commands_by_interface.items():
            commands.append('interface {}'.format(interface))
            commands.extend(interface_commands)

        return commands


def _param_diff(want, have, replace=False, remove=False):
    replace_params = {}
    remove_params = {}
    for config in want:
        key = config['name']
        for extant in have:
            if extant['name'] == key:
                break
        else:
            extant = {}

        if remove:
            remove_params[key] = dict(set(extant.items()).difference(config.items()))
        if replace:
            replace_params[key] = dict(set(config.items()).difference(extant.items()))
            if remove:
                # We won't need to also clear the configuration if we've
                # already set it to something
                for param in replace_params[key]:
                    remove_params[key].pop(param, None)

    returns = []
    if replace:
        returns.append(replace_params)
    if remove:
        returns.append(remove_params)

    return returns


def _remove_config(params):
    """
    Generates commands to reset config to defaults based on keys provided.
    """
    commands = {}
    for interface, config in params.items():
        interface_commands = []
        for param in config:
            if param == 'description':
                interface_commands.append('   no description')
            elif param == 'enable':
                interface_commands.append('   no shutdown')
        if interface_commands:
            commands[interface] = interface_commands

    return commands


def _replace_config(params):
    """
    Generates commands to replace config to new values based on provided dictionary.
    """
    commands = {}
    for interface, config in params.items():
        interface_commands = []
        for param, state in config.items():
            if param == 'description':
                interface_commands.append('   description "{}"'.format(state))
            elif param == 'enable':
                interface_commands.append('   {}shutdown'.format('no ' if state else ''))
        if interface_commands:
            commands[interface] = interface_commands

    return commands
