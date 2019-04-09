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
        want = _param_list_to_dict(want)
        have = _param_list_to_dict(have)
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
        commands = _compute_commands(want, have, replace=True, remove=True)

        replace = commands['replace']
        remove = commands['remove']

        commands_by_interface = replace
        for interface, commands in remove.items():
            commands_by_interface[interface] = replace.get(interface, []) + commands

        return _flatten_commands(commands_by_interface)

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        # Add empty desired state for unspecified interfaces
        for key in have:
            if key not in want:
                want[key] = {}

        # Otherwise it's the same as replaced
        return Interfaces._state_replaced(want, have)

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = _compute_commands(want, have, replace=True)
        return _flatten_commands(commands['replace'])

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = _compute_commands(want, have, remove=True)
        return _flatten_commands(commands['remove'])


def _param_list_to_dict(param_list):
    param_dict = {}
    for params in param_list:
        name = params.pop('name')
        param_dict[name] = params

    return param_dict


def _compute_commands(want, have, replace=False, remove=False):
    replace_params = {}
    remove_params = {}
    for name, config in want.items():
        extant = have.get(name, {})

        if remove:
            remove_params[name] = dict(set(extant.items()).difference(config.items()))
        if replace:
            replace_params[name] = dict(set(config.items()).difference(extant.items()))
            if remove:
                # We won't need to also clear the configuration if we've
                # already set it to something
                for param in replace_params[name]:
                    remove_params[name].pop(param, None)

    returns = {}
    if replace:
        returns['replace'] = _replace_config(replace_params)
    if remove:
        returns['remove'] = _remove_config(remove_params)

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
                interface_commands.append('   description "{0}"'.format(state))
            elif param == 'enable':
                interface_commands.append('   {0}shutdown'.format('no ' if state else ''))
        if interface_commands:
            commands[interface] = interface_commands

    return commands


def _flatten_commands(command_dict):
    commands = []
    for interface, interface_commands in command_dict.items():
        commands.append('interface {0}'.format(interface))
        commands.extend(interface_commands)

    return commands
