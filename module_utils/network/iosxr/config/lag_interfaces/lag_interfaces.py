#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_lag_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.facts.facts import Facts
from ansible.module_utils.network.iosxr. \
    utils.utils import search_obj_in_list, list_to_dict, diff_list_of_dicts
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import dict_diff


class Lag_interfaces(ConfigBase):
    """
    The iosxr_lag_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lag_interfaces',
    ]

    def __init__(self, module):
        super(Lag_interfaces, self).__init__(module)

    def get_lag_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
        lag_interfaces_facts = facts['ansible_network_resources'].get(
            'lag_interfaces')
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
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

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
            commands.extend(
                Lag_interfaces._state_overridden(
                    want, have
                )
            )
        elif state == 'deleted':
            commands.extend(
                Lag_interfaces._state_deleted(
                    want, have
                )
            )
        else:
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have)

                if state == 'merged':
                    commands.extend(
                        Lag_interfaces._state_merged(
                            item, obj_in_have
                        )
                    )

                elif state == 'replaced':
                    commands.extend(
                        Lag_interfaces._state_replaced(
                            item, obj_in_have
                        )
                    )

        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        if have:
            commands.extend(
                Lag_interfaces._render_bundle_del_commands(
                    want,
                    have
                )
            )

        commands.extend(
            Lag_interfaces._render_bundle_updates(
                want,
                have
            )
        )

        if commands or have == {}:
            Lag_interfaces._pad_commands(
                commands, want['name']
            )

        if have:
            commands.extend(
                Lag_interfaces._render_interface_del_commands(
                    want,
                    have
                )
            )

        commands.extend(
            Lag_interfaces._render_interface_updates(
                want,
                have
            )
        )

        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        for have_intf in have:
            intf_in_want = search_obj_in_list(have_intf['name'], want)
            if not intf_in_want:
                commands.extend(
                    Lag_interfaces._purge_attribs(have_intf)
                )

        for intf in want:
            intf_in_have = search_obj_in_list(intf['name'], have)
            commands.extend(
                Lag_interfaces._state_replaced(
                    intf,
                    intf_in_have
                )
            )

        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        if not have:
            have = {}

        commands.extend(
            Lag_interfaces._render_bundle_updates(
                want, have
            )
        )

        if commands or have == {}:
            Lag_interfaces._pad_commands(
                commands, want['name']
            )

        commands.extend(
            Lag_interfaces._render_interface_updates(
                want, have
            )
        )

        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        if not want:
            for item in have:
                commands.extend(
                    Lag_interfaces._purge_attribs(
                        intf=item
                    )
                )
        else:
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have)
                commands.extend(
                    Lag_interfaces._purge_attribs(
                        intf=obj_in_have
                    )
                )

        return commands

    @staticmethod
    def _render_bundle_updates(want_intf, have_intf):
        """ The command generator for updates to bundles

        :rtype: A list
        :returns: the commands necessary to update bundles
        """
        commands = []

        if not have_intf:
            have_intf = {}

        for item in ['mode', 'load_balancing_hash']:
            if want_intf[item] and want_intf[item] != have_intf.get(item):
                commands.append(
                    Lag_interfaces._compute_commands(
                        item, want_intf[item]))

        if want_intf['links']:
            updates = dict_diff(have_intf.get('links', {}), want_intf['links'])
            for key, value in iteritems(updates):
                commands.append(Lag_interfaces._compute_commands(key, value))

        return commands

    @staticmethod
    def _render_interface_updates(want_intf, have_intf):
        """ The command generator for updates to member
            interfaces

        :rtype: A list
        :returns: the commands necessary to update member
                interfaces
        """
        commands = []

        if not have_intf:
            have_intf = {}

        member_diff = diff_list_of_dicts(want_intf['members'], have_intf.get('members', {}))

        for diff in member_diff:
            diff_cmd = []
            bundle_cmd = 'bundle id {}'.format(want_intf['name'].split('Bundle-Ether')[1])
            if diff.get('mode'):
                bundle_cmd += ' mode {}'.format(diff.get('mode'))
            diff_cmd.append(bundle_cmd)
            Lag_interfaces._pad_commands(diff_cmd, diff['member'])
            commands.extend(diff_cmd)

        return commands

    @staticmethod
    def _render_bundle_del_commands(want_intf, have_intf):
        """ The command generator for delete commands

        :rtype: A list
        :returns: the commands necessary to delete attributes
        """
        commands = []

        for attrib in ['mode', 'load_balancing_hash']:
            if have_intf.get(attrib) and not want_intf[attrib]:
                commands.append('no {}'.format(
                    Lag_interfaces._compute_commands(attrib, have_intf[attrib])))

        if not want_intf['links']:
            want_intf['links'] = {}

        if have_intf.get('links'):
            for item in ['max_active', 'min_active']:
                if have_intf['links'].get(item) and not want_intf['links'].get(item):
                    commands.append('no {}'.format(
                        Lag_interfaces._compute_commands(item, have_intf['links'][item])))

        return commands

    @staticmethod
    def _render_interface_del_commands(want_intf, have_intf):
        commands = []

        have_members = have_intf.get('members')

        if have_members:
            have_members = list_to_dict(deepcopy(have_members), key='member')
            want_members = list_to_dict(deepcopy(want_intf).get('members', []), key='member')

            for key in have_members:
                if key not in want_members:
                    member_cmd = ['no bundle id']
                    Lag_interfaces._pad_commands(member_cmd, key)
                    commands.extend(member_cmd)

        return commands

    @staticmethod
    def _purge_attribs(intf):
        """ The command generator for purging attributes

        :rtype: A list
        :returns: the commands necessary to purge attributes
        """
        commands = []
        for attrib in ['mode', 'load_balancing_hash']:
            if intf.get(attrib):
                commands.append('no {}'.format(
                    Lag_interfaces._compute_commands(attrib, intf[attrib])))

        if intf.get('links'):
            for item in ['max_active', 'min_active']:
                if intf['links'].get(item):
                    commands.append('no {}'.format(
                        Lag_interfaces._compute_commands(item, intf['links'][item])))

        if commands:
            Lag_interfaces._pad_commands(
                commands, intf['name']
            )

        members = intf.get('members')

        if members:
            members = list_to_dict(deepcopy(members), key='member')
            for key in members:
                member_cmd = ['no bundle id']
                Lag_interfaces._pad_commands(member_cmd, key)
                commands.extend(member_cmd)

        return commands

    @staticmethod
    def _compute_commands(key, value):
        if key == "mode":
            return "lacp mode {}".format(value)

        elif key == "load_balancing_hash":
            return "bundle load-balancing hash {}".format(value)

        elif key == "max_active":
            return "bundle maximum-active links {}".format(value)

        elif key == "min_active":
            return "bundle minimum-active links {}".format(value)

    @staticmethod
    def _pad_commands(commands, interface):
        commands.insert(0, 'interface {}'.format(interface))
        commands.append('exit')
