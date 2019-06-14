#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_lag_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

'''
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.vyos.vyos import load_config, run_commands
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec
'''
from ansible.module_utils.network.common.utils import to_list, dict_diff
from ansible.module_utils.six import iteritems
from ansible.module_utils.network. \
    vyos.argspec.lag_interfaces.lag_interfaces import Lag_interfacesArgs
from ansible.module_utils.network. \
    vyos. \
    config.base import ConfigBase
from ansible.module_utils.network. \
    vyos.facts.facts import Facts

from ansible.module_utils.network. \
    vyos.utils.utils import search_obj_in_list

import q
class Lag_interfaces(ConfigBase, Lag_interfacesArgs):
    """
    The vyos_lag_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lag_interfaces',
    ]

    params = ['arp-monitor', 'hash-policy', 'members', 'mode', 'name', 'primary']
    set_cmd = 'set interfaces bonding '
    del_cmd = 'delete interfaces bonding '

    def get_lag_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts().get_facts(self._module,
                                             self._connection,
                                             self.gather_subset,
                                             self.gather_network_resources)
        lag_interfaces_facts = facts['ansible_network_resources'].get('lag_interfaces')
        if not lag_interfaces_facts:
            return []
        return lag_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()
        existing_lag_interfaces_facts = self.get_lag_interfaces_facts()
        commands.extend(self.set_config(existing_lag_interfaces_facts))
        if commands:
            if self._module.check_mode:
                resp = self._connection.edit_config(commands, commit=False)
            else:
                resp = self._connection.edit_config(commands)
            result['changed'] = True

        result['commands'] = commands

        if self._module._diff:
            result['diff'] = resp['diff'] if result['changed'] else None

        changed_lag_interfaces_facts = self.get_lag_interfaces_facts()


        result['before'] = existing_lag_interfaces_facts
        if result['changed']:
            result['after'] = changed_lag_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lag_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lag_interfaces_facts
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
            commands.extend(self._state_overridden(want=want, have=have))
        elif state == 'deleted':
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have)
                commands.extend(
                    self._state_deleted(
                        want_lag=item, have_lag=obj_in_have
                    )
                )
        elif state == 'merged':
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have)
                commands.extend(
                    self._state_merged(
                        want_lag=item, have_lag=obj_in_have
                    )
                )
        elif state == 'replaced':
            kwargs = {}
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
        return commands

    @staticmethod
    def _state_overridden(**kwargs):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        return commands

    @staticmethod
    def _state_merged(**kwargs):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        want_lag = kwargs['want_lag']
        have_lag = kwargs['have_lag']

        if have_lag:
            commands.extend(
                Lag_interfaces._render_updates(
                    want_element = {'lag': want_lag},
                    have_element = {'lag': have_lag}
                )
            )
        else:
            commands.extend(
                Lag_interfaces._render_set_commands(
                    want_element={
                        'lag': want_lag
                    }
                )
            )

        return commands

    @staticmethod
    def _state_deleted(**kwargs):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        have_lag = kwargs['have_lag']
        if have_lag:
            commands.extend(Lag_interfaces._purge_attribs(lag=have_lag))

        return commands

    @staticmethod
    def _render_updates(**kwargs):
        commands = []
        want_element = kwargs['want_element']
        have_element = kwargs['have_element']

        lag_name = have_element['lag']['name']

        set_cmd = Lag_interfaces.set_cmd + lag_name
        del_cmd = Lag_interfaces.del_cmd + lag_name
        have_item = have_element['lag']
        want_item = want_element['lag']

        name = want_item['name']
        members = want_item.get('members') or []

        updates = dict_diff(have_item, want_item)
        if updates:
            for key, value in iteritems(updates):
                if key == 'enable':
                    if value:
                        commands.append(del_cmd + ' disable')
                    else:
                        commands.append(set_cmd + ' disable')
                elif value:
                    if key == 'members':
                        for m in members:
                            commands.append('set interfaces ethernet ' + m + ' bond-group ' + name)

                    else:
                        commands.append(
                        set_cmd + ' ' + key + " '" + str(value) + "'"
                        )
        return commands


    @staticmethod
    def _render_set_commands(**kwargs):
        commands = []
        want_element = kwargs['want_element']
        set_cmd = Lag_interfaces.set_cmd + want_element['lag']['name']

        params = Lag_interfaces.params
        want_item = want_element['lag']

        for item in want_item :
            members = item.get('members') or []
            name = item['name']


        commands.append(set_cmd)
        for attrib in params:
            value = want_item[attrib]
            if value:
                if attrib == 'name':
                    commands.append(set_cmd)
                elif attrib == 'members':
                    for m in members:
                        commands.append('set interfaces ethernet ' + m + ' bond-group ' + name)

                else:
                    commands.append(
                        set_cmd + ' ' + attrib + " '" + str(value) + "'"
                    )
        return commands

    @staticmethod
    def _purge_attribs(**kwargs):
        commands = []
        lag = kwargs['lag']
        del_lag = Lag_interfaces.del_cmd + lag['name']

        for item in Lag_interfaces.params:
            if lag.get(item):
                commands.append(del_lag + ' ' + item)
            if not lag['enable']:
                commands.append(lag + ' disable')

        return commands
