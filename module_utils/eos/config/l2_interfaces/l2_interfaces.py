#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_l2_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.network.common.utils import to_list

from ansible.module_utils.eos.argspec.l2_interfaces.l2_interfaces import L2_interfacesArgs
from ansible.module_utils.eos.config.base import ConfigBase
from ansible.module_utils.eos.facts.facts import Facts


class L2_interfaces(ConfigBase, L2_interfacesArgs):
    """
    The eos_l2_interfaces class
    """

    gather_subset = [
        'net_configuration_l2_interfaces',
    ]

    def get_l2_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts = Facts().get_facts(self._module, self._connection, self.gather_subset)
        l2_interfaces_facts = facts['net_configuration'].get('l2_interfaces')
        if not l2_interfaces_facts:
            return []
        return l2_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_l2_interfaces_facts = self.get_l2_interfaces_facts()
        commands.extend(self.set_config(existing_l2_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_l2_interfaces_facts = self.get_l2_interfaces_facts()

        result['before'] = existing_l2_interfaces_facts
        if result['changed']:
            result['after'] = changed_l2_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l2_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_l2_interfaces_facts
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
        commands = []
        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for interface in want:
            for extant in have:
                if extant['name'] == interface['name']:
                    break
            else:
                continue

            intf_commands = []
            wants_access = interface["access"]
            if wants_access:
                access_vlan = wants_access.get("vlan")
                if access_vlan and access_vlan != extant["access"]["vlan"]:
                    intf_commands.append("switchport access vlan {0}".format(access_vlan))

            wants_trunk = interface["trunk"]
            if wants_trunk:
                native_vlan = wants_trunk.get("native_vlan")
                if native_vlan and native_vlan != extant["trunk"]["native_vlan"]:
                    intf_commands.append("switchport trunk native vlan {0}".format(native_vlan))

                allowed_vlans = interface['trunk'].get("trunk_allowed_vlans")
                if allowed_vlans and allowed_vlans != extant["trunk"]["trunk_allowed_vlans"]:
                    intf_commands.append("switchport trunk allowed vlan {0}".format(allowed_vlans))

            if intf_commands:
                intf_commands.insert(0, "interface {0}".format(interface['name']))
                commands.extend(intf_commands)

        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for interface in want:
            for extant in have:
                if extant['name'] == interface['name']:
                    break
            else:
                continue

            intf_commands = []
            if "access" in extant:
                intf_commands.append("no switchport access vlan")

            trunk = extant.get("trunk", {})
            if "trunk_allowed_vlans" in trunk:
                intf_commands.append("no switchport trunk allowed vlan")
            if "native_vlan" in trunk:
                intf_commands.append("no switchport trunk native vlan")

            if intf_commands:
                intf_commands.insert(0, "interface {}".format(interface["name"]))
                commands.extend(intf_commands)

        return commands
