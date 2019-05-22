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


from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list

from ansible.module_utils.ios.argspec.l2_interfaces.l2_interfaces import L2_InterfacesArgs
from ansible.module_utils.ios.config.base import ConfigBase
from ansible.module_utils.ios.facts.facts import Facts
from ansible.module_utils.ios.utils.utils import get_interface_type, normalize_interface, search_obj_in_list


class L2_Interfaces(ConfigBase, L2_InterfacesArgs):
    """
    The ios_interfaces class
    """

    gather_subset = [
        'net_configuration_interfaces',
    ]

    params = ('access', 'trunk')
    trunk_params = ('encapsulation', 'pruning_vlan', 'native_vlan', 'allowed_vlan')
    access_cmds = {'access_vlan': 'switchport access vlan', 'mode': 'switchport mode access'}
    trunk_cmds = {'encapsulation': 'switchport trunk encapsulation', 'pruning_vlan': 'switchport trunk pruning vlan',
                  'native_vlan': 'switchport trunk native vlan', 'allowed_vlan': 'switchport trunk allowed vlan',
                  'mode': 'switchport mode trunk'}

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
        result['before'] = existing_facts
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        interfaces_facts = self.get_interfaces_facts()

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
            kwargs = {'want': want, 'have': have, 'module': self._module}
            commands = L2_Interfaces._state_overridden(**kwargs)
        else:
            for w in want:
                name = w['name']
                interface_type = get_interface_type(name)
                obj_in_have = search_obj_in_list(name, have)
                kwargs = {'want': w, 'have': obj_in_have, 'type': interface_type, 'module': self._module}
                if state == 'deleted':
                    commands.extend(L2_Interfaces._state_deleted(**kwargs))

                if state == 'merged':
                    commands.extend(L2_Interfaces._state_merged(**kwargs))

                if state == 'replaced':
                    commands.extend(L2_Interfaces._state_replaced(**kwargs))

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
        name = want['name']

        if name:
            interface = 'interface ' + name
        if obj_in_have:
            for item in L2_Interfaces.params:
                candidate = want.get(item)
                if item == 'trunk' and candidate:
                    for each in L2_Interfaces.trunk_params:
                        if each == 'allowed_vlan' or each == 'pruning_vlan':
                            if candidate[0].get(each):
                                proposed = (",".join(map(str, candidate[0].get(each)))).split(',')
                            if obj_in_have.get(each):
                                value = obj_in_have.get(each).split(',')
                        else:
                            proposed = candidate[0].get(each)
                            value = obj_in_have.get(each)
                        if value and proposed != value:
                            L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.trunk_cmds.get(each),
                                                                         commands)
        commands.extend(L2_Interfaces._state_merged(**kwargs))

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
        module = kwargs['module']
        # Get the user's input interface name to be configured
        interface_want = []

        for each in want:
            interface_want.append(each.get('name'))

        for have in obj_in_have:
            name = have['name']
            obj_in_want = search_obj_in_list(name, want)
            # To delete the L2 option already configured on other interface
            if not obj_in_want:
                interface_type = get_interface_type(name)
                if interface_type.lower() == 'gigabitethernet':
                    for k, v in iteritems(have):
                        if have.get('mode') == 'access' and k != 'name':
                            interface = 'interface ' + name
                            L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.access_cmds[k],
                                                                         commands)
                        elif have.get('mode') == 'trunk' and k != 'name':
                            interface = 'interface ' + name
                            L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.trunk_cmds[k],
                                                                         commands)
            # To delete the L2 option already configured on input interface
            else:
                cmd = []
                for k, v in iteritems(have):
                    interface = 'interface ' + name
                    if obj_in_want.get('access') and k != 'name':
                        L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.access_cmds[k], cmd)
                    elif obj_in_want.get('trunk') and k != 'name':
                        L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.trunk_cmds[k], cmd)
                for each in cmd:
                    commands.append(each)
        for w in want:
            name = w['name']
            have = search_obj_in_list(name, obj_in_have)
            kwargs = {'want': w, 'have': have, 'module': module}
            cmd = L2_Interfaces._state_merged(**kwargs)
            if cmd:
                commands.extend(cmd)
            else:
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
        module = kwargs['module']
        state = module.params['state']
        if name:
            interface = 'interface ' + name
        if obj_in_have:
            for item in L2_Interfaces.params:
                candidate = want.get(item)
                if item == 'access' and candidate:
                    for each in candidate:
                        if each.get('vlan') and str(each.get('vlan')) != obj_in_have.get('access_vlan')\
                                or state == 'overridden':
                            for k,v in iteritems(L2_Interfaces.access_cmds):
                                if k == 'access_vlan':
                                    v = v + ' {}'.format(each.get('vlan'))
                                L2_Interfaces._add_command_to_interface(interface, v, commands)
                elif item == 'trunk' and candidate:
                    if obj_in_have.get('encapsulation') or candidate[0].get('encapsulation'):
                        L2_Interfaces._add_interface_switchport_trunk_cmd(state, candidate, obj_in_have, interface,
                                                                          commands)
                        if commands and 'switchport mode trunk' not in commands:
                            L2_Interfaces._add_command_to_interface(interface, 'switchport mode trunk', commands)
                    else:
                        msg = interface + " switchport trunk cannot be configured with negotiate trunking encapsulation"
                        module.fail_json(msg=msg)
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

        if obj_in_have.get('mode') and obj_in_have['mode'] == 'access':
            # delete switchport with access mode and its properties
            L2_Interfaces._remove_command_from_interface(interface, 'switchport mode', commands)
            if 'access_vlan' in obj_in_have:
                L2_Interfaces._remove_command_from_interface(interface, 'switchport access vlan', commands)
        elif obj_in_have.get('mode') and obj_in_have['mode'] == 'trunk':
            # delete switchport with trunk mode and its properties
            for item in L2_Interfaces.trunk_params:
                if obj_in_have.get(item):
                    L2_Interfaces._remove_command_from_interface(interface, L2_Interfaces.trunk_cmds[item], commands)
        return commands

    @staticmethod
    def _remove_command_from_interface(interface, cmd, commands):
        if interface not in commands:
            commands.insert(0, interface)
        if 'no switchport mode' not in commands:
            commands.insert(1, 'no switchport mode')
        commands.append('no %s' % cmd)
        return commands

    @staticmethod
    def _add_command_to_interface(interface, cmd, commands):
        if interface not in commands:
            commands.insert(0, interface)
        commands.append(cmd)

    @staticmethod
    def _add_interface_switchport_trunk_cmd(state, candidate, obj_in_have, interface, commands):
        for each in candidate:
            for item in L2_Interfaces.trunk_params:
                if item == 'encapsulation' and each.get(item) and each.get(item) != obj_in_have.get(item):
                    cmd = L2_Interfaces.trunk_cmds[item] + ' {}'.format(each.get('encapsulation'))
                    L2_Interfaces._add_command_to_interface(interface, cmd, commands)
                if item == 'native_vlan' and each.get(item) and str(each.get(item)) != obj_in_have.get(item):
                    cmd = L2_Interfaces.trunk_cmds[item] + ' {}'.format(each.get(item))
                    L2_Interfaces._add_command_to_interface(interface, cmd, commands)
                if item == 'pruning_vlan' and each.get(item):
                    pruning_vlans = (",".join(map(str, each.get(item))))
                    if pruning_vlans != obj_in_have.get(item):
                        cmd = L2_Interfaces.trunk_cmds[item] + ' {}'.format(pruning_vlans)
                        L2_Interfaces._add_command_to_interface(interface, cmd, commands)
                if item == 'allowed_vlan' and each.get(item):
                    allowed_vlan = (",".join(map(str, each.get(item))))
                    existing_vlans = vlans_to_add = None
                    if obj_in_have.get(item):
                        existing_vlans = obj_in_have.get(item).split(',')
                        vlans_to_add = set(allowed_vlan.split(',')).difference(existing_vlans)
                        vlans_to_remove = set(existing_vlans).difference(allowed_vlan.split(','))
                    if not existing_vlans and each.get(item):
                        cmd = L2_Interfaces.trunk_cmds[item] + ' {}'.format(allowed_vlan)
                        L2_Interfaces._add_command_to_interface(interface, cmd, commands)
                    elif vlans_to_add and state == 'merged':
                        cmd = L2_Interfaces.trunk_cmds[item] + ' {}'.format(allowed_vlan)
                        L2_Interfaces._add_command_to_interface(interface, cmd, commands)
                    elif vlans_to_remove and state == 'replaced':
                        cmd = L2_Interfaces.trunk_cmds[item] + ' {}'.format(allowed_vlan)
                        L2_Interfaces._add_command_to_interface(interface, cmd, commands)
