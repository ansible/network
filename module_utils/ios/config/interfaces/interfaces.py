#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 <company_name>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""


from ansible.module_utils.six import iteritems
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
        'net_configuration_interfaces',
    ]
    params = ('description', 'mtu', 'speed', 'duplex')

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

        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        interfaces_facts = self.get_interfaces_facts()

        result['before'] = interfaces_facts
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
        have = existing_facts#self.get_interfaces_facts()
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
            commands = Interfaces._state_overridden(**kwargs)
        else:
            for w in want:
                name = w['name']
                interface_type = get_interface_type(name)
                obj_in_have = search_obj_in_list(name, have)
                kwargs = {'want': w, 'have': obj_in_have, 'type': interface_type}
                if state == 'deleted':
                    commands.extend(Interfaces._state_deleted(**kwargs))

                if state == 'merged':
                    commands.extend(Interfaces._state_merged(**kwargs))

                if state == 'replaced':
                    commands.extend(Interfaces._state_replaced(**kwargs))

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
        obj_in_have = kwargs['have']
        interface_type = kwargs['type']

        if want['name']:
            interface = 'interface ' + want['name']

        if obj_in_have:
            if interface_type.lower() == 'loopback':
                commands.extend(Interfaces._state_merged(want, obj_in_have))
            elif interface_type.lower() == 'gigabitethernet':
                for item in Interfaces.params:
                    value = obj_in_have.get(item)
                    if value and want[item] != value and value != 'auto':
                        Interfaces._remove_command_from_interface(interface, item, commands)
        kwargs = {'want': want, 'have': obj_in_have}
        commands.extend(Interfaces._state_merged(**kwargs))

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
        obj_in_have = kwargs['have']
        interface_want = 'interface ' + want[0]['name']

        for have in obj_in_have:
            name = have['name']
            obj_in_want = search_obj_in_list(name, want)
            if not obj_in_want:
                interface_type = get_interface_type(name)
                if interface_type.lower() == 'loopback':
                    commands.append('interface ' + name)
                    commands.append('no description')
                elif interface_type.lower() == 'gigabitethernet':
                    default = True
                    if have['enabled'] is True:
                        for k, v in iteritems(have):
                            if k in Interfaces.params:
                                if have[k] is not None:
                                    default = False
                                    break
                    else:
                        default = False
                    if default is False:
                        # Delete the configurable params by interface module
                        interface = 'interface ' + name
                        for each in Interfaces.params:
                            if interface not in commands:
                                commands.append(interface)
                            commands.append('no {0}'.format(each))
            else:
                changed = False
                # Delete the wanted interface to be replaced with provided values
                for k, v in iteritems(have):
                    if obj_in_want[k] != have[k] and have[k] != "auto":
                        if interface_want not in commands:
                            changed = True
                            commands.append(interface_want)
                        commands.append('no {0}'.format(k))
                if not changed:
                    break

        if interface_want in commands:
            # if there's change in interface_want then extend the commands
            for w in want:
                name = w['name']
                have = search_obj_in_list(name, obj_in_have)
                kwargs = {'want': w, 'have': have}
                commands.extend(Interfaces._state_merged(**kwargs))
        else:
            # if there's no change in inteface_want then maintain idempotency
            commands = []

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
        obj_in_have = kwargs['have']
        name = want['name']
        enabled = want.get('enabled')

        if name:
            interface = 'interface ' + name
        if not obj_in_have:
            commands.append(interface)
            commands.append('no shutdown') if enabled else commands.append('shutdown')

            for item in Interfaces.params:
                candidate = want.get(item)
                if candidate:
                    commands.append(item + ' ' + str(candidate))
        else:
            if enabled is True and enabled != obj_in_have.get('enabled'):
                Interfaces._add_command_to_interface(interface, 'no shutdown', commands)
            elif enabled is False and enabled != obj_in_have.get('enabled'):
                Interfaces._add_command_to_interface(interface, 'shutdown', commands)
            for item in Interfaces.params:
                candidate = want.get(item)
                if candidate and candidate != obj_in_have.get(item):
                    cmd = item + ' ' + str(candidate)
                    Interfaces._add_command_to_interface(interface, cmd, commands)

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
        obj_in_have = kwargs['have']
        interface_type = kwargs['type']
        if not obj_in_have or interface_type == 'unknown':
            return commands

        interface = 'interface ' + want['name']

        if 'description' in obj_in_have:
            Interfaces._remove_command_from_interface(interface, 'description', commands)
        if 'enabled' in obj_in_have and obj_in_have['enabled'] is False:
            # if enable is False set enable as True which is the default behavior
            Interfaces._remove_command_from_interface(interface, 'shutdown', commands)

        if interface_type.lower() == 'gigabitethernet':
            if 'speed' in obj_in_have and obj_in_have['speed'] != 'auto':
                Interfaces._remove_command_from_interface(interface, 'speed', commands)
            if 'duplex' in obj_in_have and obj_in_have['duplex'] != 'auto':
                Interfaces._remove_command_from_interface(interface, 'duplex', commands)
            if 'mtu' in obj_in_have:
                Interfaces._remove_command_from_interface(interface, 'mtu', commands)

        return commands

    @staticmethod
    def _remove_command_from_interface(interface, cmd, commands):
        #print interface, cmd, commands
        if interface not in commands:
            commands.insert(0, interface)
        commands.append('no %s' % cmd)
        return commands

    @staticmethod
    def _add_command_to_interface(interface, cmd, commands):
        if interface not in commands:
            commands.insert(0, interface)
        commands.append(cmd)
