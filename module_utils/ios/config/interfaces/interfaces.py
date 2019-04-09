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

from ansible.module_utils.ios.argspec.interfaces.interfaces import InterfaceArgs
from ansible.module_utils.ios.config.base import ConfigBase
from ansible.module_utils.ios.facts.facts import Facts
from ansible.module_utils.ios.utils.utils import get_interface_type, normalize_interface, search_obj_in_list
import q

class Interfaces(ConfigBase, InterfacesArgs):
    """
    The ios_interfaces class
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
        :returns: The result from moduel execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_facts = self.get_interface_facts()

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
        q(want)
        for w in want:
            w.update({'name': normalize_interface(w['name'])})
        have = existing_facts#self.get_interfaces_facts()
        resp = self.set_state(want, have)
        q(resp)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = list()

        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        else:
            for w in want:
                name = w['name']
                interface_type = get_interface_type(name)
                obj_in_have = search_obj_in_list(name, have)

                if state == 'deleted':
                    commands.extend(self._state_deleted(w, obj_in_have, interface_type))

                if state == 'merged':
                    commands.extend(self._state_merged(w, obj_in_have, interface_type))

                if state == 'replaced':
                    commands.extend(self._state_replaced(w, obj_in_have, interface_type))
        return commands

    @staticmethod
    def _state_replaced(want, obj_in_have, interface_type):
        """ The command generator when state is replaced

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = list()
        if interface_type in ('loopback', 'portchannel', 'svi'):
            commands.append('no interface {0}'.format(want['name']))
            commands.extend(Interfaces._state_merged(want, obj_in_have, interface_type))
        else:
            commands.append('default interface {0}'.format(want['name']))
            commands.extend(Interfaces._state_merged(want, obj_in_have, interface_type))
        # if want != have:
        #     # compare and generate command set
        #     pass

        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        # if want != have:
        #     pass
        commands = list()

        for h in have:
            name = h['name']
            obj_in_want = search_obj_in_list(name, want)
            if not obj_in_want:
                interface_type = get_interface_type(name)
                if interface_type == 'ethernet':
                    default = True
                    if h['enabled'] is True:
                        keys = ('description', 'mode', 'mtu', 'speed', 'duplex')
                        for k, v in iteritems(h):
                            if k in keys:
                                if h[k] is not None:
                                    default = False
                                    break
                    else:
                        default = False

                    if default is False:
                        # Chan interface to its default state
                        commands.append('default interface {0}'.format(name))

        return commands

    @staticmethod
    def _state_merged(want, have, obj_in_have, interface_type):
        """ The command generator when state is merged

        :param want: the additive configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """

        commands = []

        args = ('speed', 'description', 'duplex', 'mtu')
        name = want['name']
        mode = want.get('mode')

        if name:
            interface = 'interface ' + name

        if not obj_in_have:
            commands.append(interface)
            if interface_type in ('ethernet', 'portchannel'):
                pass

        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :param want: the objects from which the configuration should be removed
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        if want != have:
            pass
        commands = []
        return commands


