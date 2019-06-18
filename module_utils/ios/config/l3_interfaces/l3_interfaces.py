#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_l3_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.utils import is_netmask, is_masklen, to_netmask, to_masklen
from ansible.module_utils.six import iteritems

from ansible.module_utils.ios.argspec.l3_interfaces.l3_interfaces import L3_InterfacesArgs
from ansible.module_utils.ios.config.base import ConfigBase
from ansible.module_utils.ios.facts.facts import Facts
import q

class L3_Interfaces(ConfigBase, L3_InterfacesArgs):
    """
    The ios_l3_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l3_interfaces'
    ]

    def get_l3_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)
        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        result = Facts().get_facts(self._module, self._connection, self.gather_subset, self.gather_network_resources)
        facts = result
        l3_interfaces_facts = facts['ansible_network_resources'].get('l3_interfaces')

        if not l3_interfaces_facts:
            return []
        return l3_interfaces_facts

    def execute_module(self):
        """ Execute the module
        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_l3_interfaces_facts = self.get_l3_interfaces_facts()
        commands.extend(self.set_config(existing_l3_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_l3_interfaces_facts = self.get_l3_interfaces_facts()

        result['before'] = existing_l3_interfaces_facts
        if result['changed']:
            result['after'] = changed_l3_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l3_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_l3_interfaces_facts
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
            kwargs = {'want': want, 'have': have, 'module': self._module}
            commands = self._state_overridden(**kwargs)
        elif state == 'deleted':
            kwargs = {'want': want, 'have': have, 'module': self._module}
            commands = self._state_deleted(**kwargs)
        elif state == 'merged':
            kwargs = {'want': want, 'have': have, 'module': self._module}
            commands = self._state_merged(**kwargs)
        elif state == 'replaced':
            kwargs = {'want': want, 'have': have, 'module': self._module}
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
        want = kwargs['want']
        have = kwargs['have']
        module = kwargs['module']

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                continue
            kwargs = {'want': interface, 'have': each, }
            commands.extend(L3_Interfaces.clear_interface(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands, 'module': module}
            commands.extend(L3_Interfaces.set_interface(**kwargs))
        # Remove the duplicate interface call
        commands = L3_Interfaces._remove_duplicate_interface(commands)

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
        module = kwargs['module']

        for each in have:
            for interface in want:
                if each['name'] == interface['name']:
                    break
            else:
                # We didn't find a matching desired state, which means we can
                # pretend we recieved an empty desired state.
                interface = dict(name=each['name'])
                kwargs = {'want': interface, 'have': each}
                commands.extend(L3_Interfaces.clear_interface(**kwargs))
                continue
            kwargs = {'want': interface, 'have': each}
            commands.extend(L3_Interfaces.clear_interface(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands, 'module': module}
            commands.extend(L3_Interfaces.set_interface(**kwargs))
        # Remove the duplicate interface call
        commands = L3_Interfaces._remove_duplicate_interface(commands)

        return commands

    @staticmethod
    def _state_merged(**kwargs):
        """ The command generator when state is merged
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        module = kwargs['module']

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                continue
            kwargs = {'want': interface, 'have': each, 'module': module}
            commands.extend(L3_Interfaces.set_interface(**kwargs))

        return commands

    @staticmethod
    def _state_deleted(**kwargs):
        """ The command generator when state is deleted
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        want = kwargs['want']
        have = kwargs['have']

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
                elif interface['name'] in each['name']:
                    break
            else:
                continue
            interface = dict(name=interface['name'])
            kwargs = {'want': interface, 'have': each}
            commands.extend(L3_Interfaces.clear_interface(**kwargs))

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
    def validate_ipv4(value, module):
        if value:
            address = value.split('/')
            if len(address) != 2:
                module.fail_json(msg='address format is <ipv4 address>/<mask>, got invalid format {}'.format(value))

            if not is_masklen(address[1]):
                module.fail_json(msg='invalid value for mask: {}, mask should be in range 0-32'.format(address[1]))

    @staticmethod
    def validate_ipv6(value, module):
        if value:
            address = value.split('/')
            if len(address) != 2:
                module.fail_json(msg='address format is <ipv6 address>/<mask>, got invalid format {}'.format(value))
            else:
                if not 0 <= int(address[1]) <= 128:
                    module.fail_json(msg='invalid value for mask: {}, mask should be in range 0-128'.format(address[1]))

    @staticmethod
    def validate_n_expand_ipv4(module, want):
        # Check if input IPV4 is valid IP and expand IPV4 with its subnet mask
        ip_addr_want = want.get('address')
        L3_Interfaces.validate_ipv4(ip_addr_want, module)
        ip = ip_addr_want.split('/')
        if len(ip) == 2:
            ip_addr_want = '{0} {1}'.format(ip[0], to_netmask(ip[1]))

        return ip_addr_want

    @staticmethod
    def _remove_duplicate_interface(commands):
        # Remove duplicate interface from commands
        set_cmd = []
        for each in commands:
            if 'interface' in each:
                interface = each
                if interface not in set_cmd:
                    set_cmd.append(each)
            else:
                set_cmd.append(each)

        return set_cmd

    @staticmethod
    def set_interface(**kwargs):
        # Set the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        module = kwargs['module']
        interface = 'interface ' + want['name']

        # To handle Sub-Interface if encapsulation is not already configured
        if '.' in want['name']:
            if not have.get('encapsulation'):
                module.fail_json(msg='IP routing on a LAN Sub-Interface is only allowed if Encapsulation'
                                     ' is configured over respective Sub-Interface'.format(want['name']))
        # To handle L3 IPV4 configuration
        if want.get("ipv4"):
            for each in want.get("ipv4"):
                if each.get('address') != 'dhcp':
                    ip_addr_want = L3_Interfaces.validate_n_expand_ipv4(module, each)
                    each['address'] = ip_addr_want

        want_ipv4 = set(tuple({k:v for k,v in iteritems(address) if v is not None}.items()) for address in want.get("ipv4") or [])
        have_ipv4 = set(tuple(address.items()) for address in have.get("ipv4") or [])
        diff = want_ipv4 - have_ipv4
        for address in diff:
            address = dict(address)
            if address.get('address') != 'dhcp':
                cmd = "ip address {}".format(address["address"])
                if address.get("secondary"):
                    cmd += " secondary"
            elif address.get('address') == 'dhcp':
                if address.get('dhcp_client') and address.get('dhcp_hostname'):
                    cmd = "ip address dhcp client-id GigabitEthernet 0/{} hostname {}".format\
                        (address.get('dhcp_client'),address.get('dhcp_hostname'))
                elif address.get('dhcp_client') and not address.get('dhcp_hostname'):
                    cmd = "ip address dhcp client-id GigabitEthernet 0/{}".format(address.get('dhcp_client'))
                elif not address.get('dhcp_client') and address.get('dhcp_hostname'):
                    cmd = "ip address dhcp hostname {}".format(address.get('dhcp_client'))

            L3_Interfaces._add_command_to_interface(interface, cmd, commands)

        # To handle L3 IPV6 configuration
        want_ipv6 = set(tuple({k:v for k,v in iteritems(address) if v is not None}.items()) for address in want.get("ipv6") or [])
        have_ipv6 = set(tuple(address.items()) for address in have.get("ipv6") or [])
        diff = want_ipv6 - have_ipv6
        for address in diff:
            address = dict(address)
            L3_Interfaces.validate_ipv6(address.get('address'), module)
            cmd = "ipv6 address {}".format(address.get('address'))
            L3_Interfaces._add_command_to_interface(interface, cmd, commands)

        return commands

    @staticmethod
    def clear_interface(**kwargs):
        # Delete the interface config based on the want and have config
        count = 0
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        interface = 'interface ' + want['name']

        if have.get('ipv4') and want.get('ipv4'):
            for each in have.get('ipv4'):
                if each.get('secondary') and not (want.get('ipv4')[count].get('secondary')):
                    cmd = 'ipv4 address {} secondary'.format(each.get('address'))
                    L3_Interfaces._remove_command_from_interface(interface, cmd, commands)
                count += 1
        if have.get('ipv4') and not want.get('ipv4'):
            L3_Interfaces._remove_command_from_interface(interface, 'ip address', commands)
        if have.get('ipv6') and not want.get('ipv6'):
            L3_Interfaces._remove_command_from_interface(interface, 'ipv6 address', commands)

        return commands
