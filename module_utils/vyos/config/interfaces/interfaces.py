#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils. \
     vyos.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils. \
     vyos. \
     config.base import ConfigBase
from ansible.module_utils. \
     vyos.facts.facts import Facts
from ansible.module_utils. \
    vyos.utils.utils import search_obj_in_list, get_interface_type


class Interfaces(ConfigBase, InterfacesArgs):
    """
    The vyos_interfaces class
    """

    gather_subset = [
        'net_configuration_interfaces',
    ]

    params = ('speed', 'description', 'duplex', 'mtu')

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

        existing_interface_facts = self.get_interfaces_facts()
        commands.extend(self.set_config())
        if commands:
            if self._module.check_mode:
                resp = self._connection.edit_config(commands, commit=False)
            else:
                resp = self._connection.edit_config(commands)
            result['changed'] = True

        result['commands'] = commands

        if self._module._diff:
            result['diff'] = resp['diff'] if result['changed'] else None

        changed_interfaces_facts = self.get_interfaces_facts()

        result['before'] = existing_interface_facts
        if result['changed']:
            result['after'] = changed_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        for w in want:
            if 'name' in w:
                w.update({'name': w['name']})
        have = self.get_interfaces_facts()
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
            commands.extend(Interfaces._state_overridden(want=want, have=have))
        else:
            for w in want:
                name = w['name']
                obj_in_have = search_obj_in_list(name, have)
                if state == 'deleted':
                    commands.extend(Interfaces._state_deleted(want_intf=w, have_intf=obj_in_have))

                elif state == 'merged':
                    commands.extend(Interfaces._state_merged(want_intf=w, have_intf=obj_in_have))

                elif state == 'replaced':
                    commands.extend(Interfaces._state_replaced(want_intf=w, have_intf=obj_in_have))

        return commands

    @staticmethod
    def _state_replaced(**kwargs):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        w = kwargs['want_intf']
        obj_in_have = kwargs['have_intf']

        name = w['name']
        delete_interface = 'delete interfaces ethernet ' + name

        if obj_in_have:
            for item in Interfaces.params:
                value = obj_in_have.get(item)
                if value and w[item] != value:
                    commands.append(delete_interface + ' ' + item + " '" + value + "'")
            if obj_in_have['enable'] != w['enable']:
                commands.append(delete_interface + ' disable')

        commands.extend(Interfaces._state_merged(want_intf=w, have_intf=obj_in_have))

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

        for h in have:
            name = h['name']
            obj_in_want = search_obj_in_list(name, want)

            delete_interface = 'delete interfaces ethernet ' + name

            if not obj_in_want:
                for item in Interfaces.params:
                    if h.get(item):
                        commands.append(delete_interface + ' ' + item)

        for w in want:
            name = w['name']
            obj_in_have = search_obj_in_list(name, have)
            commands.extend(Interfaces._state_replaced(want_intf=w, have_intf=obj_in_have))

        return commands

    @staticmethod
    def _state_merged(**kwargs):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        w = kwargs['want_intf']
        obj_in_have = kwargs['have_intf']

        name = w['name']
        set_interface = 'set interfaces ethernet ' + name
        delete_interface = 'delete interfaces ethernet ' + name

        if obj_in_have:
            for item in Interfaces.params:
                value = w[item]
                if value and str(value) != obj_in_have.get(item):
                    commands.append(set_interface + ' ' + item + " '" + value + "'")

            if w['enable'] and not obj_in_have['enable']:
                commands.append(delete_interface + ' disable')

            elif not w['enable'] and obj_in_have['enable']:
                commands.append(set_interface + ' disable')

        else:
            commands.append(set_interface)
            for item in Interfaces.params:
                value = w[item]
                if value:
                    commands.append(set_interface + ' ' + item + " '" + value + "'")

            if not w['enable']:
                commands.append(set_interface + ' disable')

        return commands

    @staticmethod
    def _state_deleted(**kwargs):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        w = kwargs['want_intf']
        obj_in_have = kwargs['have_intf']

        name = w['name']
        delete_interface = 'delete interfaces ethernet ' + name

        if obj_in_have:
            for item in Interfaces.params:
                if obj_in_have.get(item):
                    commands.append(delete_interface + ' ' + item)
            if not obj_in_have.get('enable'):
                commands.append(delete_interface + ' disable')

        return commands
