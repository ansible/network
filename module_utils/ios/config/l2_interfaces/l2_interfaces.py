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
    trunk_cmds = {'encapsulation': 'switchport trunk encapsulation', 'pruning_vlan': 'switchport trunk pruning vlan',
                  'native_vlan': 'switchport trunk native vlan', 'allowed_vlan': 'switchport trunk allowed vlan'}

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
                        if each == 'allowed_vlan':
                            if candidate[0].get(each):
                                proposed = (",".join(map(str, candidate[0].get(each)))).split(',')
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
                            if k in L2_Interfaces.params:
                                if have[k] is not None:
                                    default = False
                                    break
                    else:
                        default = False
                    if default is False:
                        # Delete the configurable params by interface module
                        interface = 'interface ' + name
                        for each in L2_Interfaces.params:
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
                commands.extend(L2_Interfaces._state_merged(**kwargs))
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
        module = kwargs['module']
        state = module.params['state']
        if name:
            interface = 'interface ' + name

        if obj_in_have:
            for item in L2_Interfaces.params:
                candidate = want.get(item)
                if item == 'access' and candidate:
                    for each in candidate:
                        if each.get('vlan') and str(each.get('vlan')) != obj_in_have.get('access_vlan'):
                            if 'switchport mode access' not in commands:
                                L2_Interfaces._add_command_to_interface(interface,'switchport mode access', commands)
                            cmd = 'switchport access vlan {}'.format(each.get('vlan'))
                            L2_Interfaces._add_command_to_interface(interface, cmd, commands)
                elif item == 'trunk' and candidate:
                    if obj_in_have.get('encapsulation') or candidate[0].get('encapsulation'):
                        L2_Interfaces._add_interface_switchport_trunk_cmd(state, candidate, obj_in_have, interface, commands)
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
            L2_Interfaces._remove_command_from_interface(interface, 'switchport mode', commands)
            if 'allowed_vlan' in obj_in_have:
                L2_Interfaces._remove_command_from_interface(interface, 'switchport trunk allowed vlan', commands)
            if 'native_vlan' in obj_in_have:
                L2_Interfaces._remove_command_from_interface(interface, 'switchport trunk native vlan', commands)
            if 'pruning_vlan' in obj_in_have:
                L2_Interfaces._remove_command_from_interface(interface, 'switchport trunk pruning vlan', commands)
            if 'encapsulation' in obj_in_have:
                L2_Interfaces._remove_command_from_interface(interface, 'switchport trunk encapsulation', commands)

        return commands

    @staticmethod
    def _remove_command_from_interface(interface, cmd, commands):
        if interface not in commands:
            commands.insert(0, interface)
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
            if each.get('encapsulation') and each.get('encapsulation') != obj_in_have.get('encapsulation'):
                cmd = 'switchport trunk encapsulation {}'.format(each.get('encapsulation'))
                L2_Interfaces._add_command_to_interface(interface, cmd, commands)
                L2_Interfaces._add_command_to_interface(interface, 'switchport mode trunk', commands)
            if each.get('native_vlan') and str(each.get('native_vlan')) != obj_in_have.get('native_vlan'):
                cmd = 'switchport trunk native vlan {}'.format(each.get('native_vlan'))
                L2_Interfaces._add_command_to_interface(interface, cmd, commands)
            if each.get('pruning_vlan'):
                pruning_vlans = (",".join(map(str, each.get('pruning_vlan'))))
                if pruning_vlans != obj_in_have.get('pruning_vlan'):
                    cmd = 'switchport trunk pruning vlan {}'.format(pruning_vlans)
                    L2_Interfaces._add_command_to_interface(interface, cmd, commands)
            if each.get('allowed_vlan'):
                allowed_vlan = (",".join(map(str, each.get('allowed_vlan'))))
                existing_vlans = vlans_to_add = None
                if obj_in_have.get('allowed_vlan'):
                    existing_vlans = obj_in_have.get('allowed_vlan').split(',')
                    vlans_to_add = set(allowed_vlan.split(',')).difference(existing_vlans)
                    vlans_to_remove = set(existing_vlans).difference(allowed_vlan.split(','))
                if not existing_vlans and each.get('allowed_vlan'):
                    cmd = 'switchport trunk allowed vlan {}'.format(allowed_vlan)
                    L2_Interfaces._add_command_to_interface(interface, cmd, commands)
                elif vlans_to_add and state == 'merged':
                    cmd = 'switchport trunk allowed vlan add {}'.format(allowed_vlan)
                    L2_Interfaces._add_command_to_interface(interface, cmd, commands)
                elif vlans_to_remove and state == 'replaced' or state == 'overridden':
                    cmd = 'switchport trunk allowed vlan {}'.format(allowed_vlan)
                    L2_Interfaces._add_command_to_interface(interface, cmd, commands)
