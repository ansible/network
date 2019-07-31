#
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

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts
from ansible.module_utils.network.ios.utils.utils import get_interface_type, dict_diff
from ansible.module_utils.network.ios.utils.utils import remove_command_from_interface, add_command_to_interface
from ansible.module_utils.network.ios.utils.utils import filter_dict_having_none_value, remove_duplicate_interface
import q

class Interfaces(ConfigBase):
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

    def __init__(self, module):
        super(Interfaces, self).__init__(module)

    def get_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
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
                  to the deisred configuration
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
                  to the deisred configuration
        """
        commands = []
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

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :param interface_type: interface type
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = []

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
                elif interface['name'] in each['name']:
                    break
            else:
                continue
            have_dict = filter_dict_having_none_value(interface, each)
            kwargs = {'want': {}, 'have': have_dict}
            commands.extend(Interfaces._clear_config(**kwargs))
            kwargs = {'want': interface, 'have': each}
            commands.extend(Interfaces._set_config(**kwargs))
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :param want: the desired configuration as a dictionary
        :param obj_in_have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

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
                commands.extend(Interfaces._clear_config(**kwargs))
                continue
            have_dict = filter_dict_having_none_value(interface, each)
            kwargs = {'want': {}, 'have': have_dict}
            commands.extend(Interfaces._clear_config(**kwargs))
            kwargs = {'want': interface, 'have': each}
            commands.extend(Interfaces._set_config(**kwargs))
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :param want: the additive configuration as a dictionary
        :param obj_in_have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                continue
            kwargs = {'want': interface, 'have': each}
            commands.extend(Interfaces._set_config(**kwargs))

        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :param want: the objects from which the configuration should be removed
        :param obj_in_have: the current configuration as a dictionary
        :param interface_type: interface type
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        if want:
            for interface in want:
                for each in have:
                    if each['name'] == interface['name']:
                        break
                else:
                    continue
                interface = dict(name=interface['name'])
                kwargs = {'want': interface, 'have': each}
                commands.extend(Interfaces._clear_config(**kwargs))
        else:
            for each in have:
                kwargs = {'want': {}, 'have': each}
                commands.extend(Interfaces._clear_config(**kwargs))

        return commands

    @staticmethod
    def _set_config(**kwargs):
        # Set the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        interface = 'interface ' + want['name']
        q(want, have, interface)

        # if want.get('enabled') and want.get('enabled') != have.get('enabled'):
        #     add_command_to_interface(interface, 'no shutdown', commands)
        # elif not want.get('enabled') and want.get('enabled') != have.get('enabled'):
        #     add_command_to_interface(interface, 'shutdown', commands)
        # Get the diff b/w want and have
        want_dict = dict_diff(want)
        have_dict = dict_diff(have)
        diff = want_dict - have_dict
        q(want_dict, have_dict, diff)
        if diff:
            diff = dict(diff)
            for item in Interfaces.params:
                if diff.get(item):
                    cmd = item + ' ' + str(want.get(item))
                    add_command_to_interface(interface, cmd, commands)
            if diff.get('enabled'):# and want.get('enabled') != have.get('enabled'):
                add_command_to_interface(interface, 'no shutdown', commands)
            elif diff.get('enabled') is False:
                add_command_to_interface(interface, 'shutdown', commands)

        return commands

    @staticmethod
    def _clear_config(**kwargs):
        # Delete the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        if want.get('name'):
            interface_type = get_interface_type(want['name'])
            interface = 'interface ' + want['name']
        else:
            interface_type = get_interface_type(have['name'])
            interface = 'interface ' + have['name']

        if have.get('description') and want.get('description') != have.get('description'):
            remove_command_from_interface(interface, 'description', commands)
        if not have.get('enabled') and want.get('enabled') != have.get('enabled'):
            # if enable is False set enable as True which is the default behavior
            remove_command_from_interface(interface, 'shutdown', commands)

        if interface_type.lower() == 'gigabitethernet':
            if have.get('speed') and have.get('speed') != 'auto' and want.get('speed') != have.get('speed'):
                remove_command_from_interface(interface, 'speed', commands)
            if have.get('duplex') and have.get('duplex') != 'auto' and want.get('duplex') != have.get('duplex'):
                remove_command_from_interface(interface, 'duplex', commands)
            if have.get('mtu') and want.get('mtu') != have.get('mtu'):
                remove_command_from_interface(interface, 'mtu', commands)

        return commands
