#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_vlans class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.six import iteritems

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts


class Vlans(ConfigBase):
    """
    The ios_vlans class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'interfaces',
    ]

    def __init__(self, module):
        super(Vlans, self).__init__(module)

    def get_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        interfaces_facts = facts['ansible_network_resources'].get('vlans')
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
                  to the desired configuration
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
                  to the desired configuration
        """
        state = self._module.params['state']
        if state == 'overridden':
            kwargs = {'want': want, 'have': have}
            commands = self._state_overridden(**kwargs)
        elif state == 'deleted':
            kwargs = {'want': want, 'have': have, 'state': state}
            commands = self._state_deleted(**kwargs)
        elif state == 'merged':
            kwargs = {'want': want, 'have': have}
            commands = self._state_merged(**kwargs)
        elif state == 'replaced':
            kwargs = {'want': want, 'have': have}
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

        check = False
        for each in want:
            for every in have:
                if every['vlan_id'] == each['vlan_id']:
                    check = True
                    break
                else:
                    continue
            if check:
                kwargs = {'want': each, 'have': every}
            else:
                kwargs = {'want': each, 'have': {}}
            commands.extend(Vlans.clear_interface(**kwargs))
            commands.extend(Vlans.set_interface(**kwargs))
        # Remove the duplicate interface call
        commands = Vlans._remove_duplicate_interface(commands)

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

        check = False
        for every in have:
            for each in want:
                if each['vlan_id'] == every['vlan_id']:
                    check = True
                    break
            else:
                # We didn't find a matching desired state, which means we can
                # pretend we recieved an empty desired state.
                #interface = dict(name=each['name'])
                kwargs = {'want': each, 'have': every}
                commands.extend(Vlans.clear_interface(**kwargs))
                continue
            if check:
                kwargs = {'want': each, 'have': every}
            else:
                kwargs = {'want': each, 'have': {}}
            commands.extend(Vlans.clear_interface(**kwargs))
            commands.extend(Vlans.set_interface(**kwargs))
        # Remove the duplicate interface call
        commands = Vlans._remove_duplicate_interface(commands)

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

        check = False
        for each in want:
            for every in have:
                if each.get('vlan_id') == every.get('vlan_id'):
                    check = True
                    break
                else:
                    continue
            if check:
                kwargs = {'want': each, 'have': every}
            else:
                kwargs = {'want': each, 'have': {}}
            commands.extend(Vlans.set_interface(**kwargs))

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
        state = kwargs['state']

        check = False
        for each in want:
            for every in have:
                if each.get('vlan_id') == every.get('vlan_id'):
                    check = True
                    break
                else:
                    continue
            if check:
                kwargs = {'want': each, 'have': every, 'state': state}
            else:
                kwargs = {'want': each, 'have': {}, 'state': state}
            commands.extend(Vlans.clear_interface(**kwargs))

        return commands

    @staticmethod
    def _remove_command_from_interface(vlan, cmd, commands):
        if vlan not in commands and cmd != 'vlan':
            commands.insert(0, vlan)
        elif cmd == 'vlan':
            commands.append('no %s' % vlan)
            return commands
        commands.append('no %s' % cmd)
        return commands

    @staticmethod
    def _add_command_to_interface(vlan_id, cmd, commands):
        if vlan_id not in commands:
            commands.insert(0, vlan_id)
        if cmd not in commands:
            commands.append(cmd)

    @staticmethod
    def _remove_duplicate_interface(commands):
        # Remove duplicate interface from commands
        set_cmd = []
        for each in commands:
            if 'vlan' in each:
                vlan = each
                if vlan not in set_cmd:
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
        vlan = 'vlan {}'.format(want.get('vlan_id'))

        # Get the diff b/w want n have
        want_dict = set(tuple({k: v for k, v in iteritems(want) if v is not None}.items()))
        have_dict = set(tuple({k: v for k, v in iteritems(have) if v is not None}.items()))
        diff = want_dict - have_dict

        if diff:
            name = dict(diff).get('name')
            state = dict(diff).get('state')
            shutdown = dict(diff).get('shutdown')
            mtu = dict(diff).get('mtu')
            remote_span = dict(diff).get('remote_span')
            if name:
                cmd = 'name {}'.format(name)
                Vlans._add_command_to_interface(vlan, cmd, commands)
            if state:
                cmd = 'state {}'.format(state)
                Vlans._add_command_to_interface(vlan, cmd, commands)
            if mtu:
                cmd = 'mtu {}'.format(mtu)
                Vlans._add_command_to_interface(vlan, cmd, commands)
            if remote_span:
                Vlans._add_command_to_interface(vlan, 'remote-span', commands)
            if shutdown:
                Vlans._add_command_to_interface(vlan, 'shutdown', commands)

        return commands

    @staticmethod
    def clear_interface(**kwargs):
        # Delete the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        state = kwargs['state']
        vlan = 'vlan {}'.format(have.get('vlan_id'))

        if have.get('vlan_id') and (have.get('vlan_id') != want.get('vlan_id') or state == 'deleted'):
            Vlans._remove_command_from_interface(vlan, 'vlan', commands)
        else:
            if have.get('mtu') != want.get('mtu'):
                Vlans._remove_command_from_interface(vlan, 'mtu', commands)
            if have.get('remote_span') != want.get('remote_span') and want.get('remote_span'):
                Vlans._remove_command_from_interface(vlan, 'remote-span', commands)
            if have.get('shutdown') != want.get('shutdown') and want.get('shutdown'):
                Vlans._remove_command_from_interface(vlan, 'shutdown', commands)
            if have.get('state') != want.get('state') and want.get('state'):
                Vlans._remove_command_from_interface(vlan, 'state', commands)

        return commands
