#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_lag_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

import re
from ansible.module_utils.six import iteritems

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts


class Lag_interfaces(ConfigBase):
    """
    The ios_lag_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'interfaces',
    ]

    def __init__(self, module):
        super(Lag_interfaces, self).__init__(module)

    def get_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        interfaces_facts = facts['ansible_network_resources'].get('lag_interfaces')
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
        module = self._module
        if state == 'overridden':
            kwargs = {'want': want, 'have': have, 'module': module}
            commands = self._state_overridden(**kwargs)
        elif state == 'deleted':
            kwargs = {'want': want, 'have': have, 'state': state}
            commands = self._state_deleted(**kwargs)
        elif state == 'merged':
            kwargs = {'want': want, 'have': have, 'module': module}
            commands = self._state_merged(**kwargs)
        elif state == 'replaced':
            kwargs = {'want': want, 'have': have, 'module': module}
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
            for each_interface in interface.get('members'):
                for each in have:
                    if each['members']:
                        if each['members'][0]['member'] == each_interface['member']:
                            break
                else:
                    continue
                kwargs = {'want': interface, 'have': each}
                commands.extend(Lag_interfaces.clear_interface(**kwargs))
                kwargs = {'want': interface, 'have': each, 'module': module}
                commands.extend(Lag_interfaces.set_interface(**kwargs))
        # Remove the duplicate interface call
        commands = Lag_interfaces._remove_duplicate_interface(commands)

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

        for interface in want:
            for each_interface in interface.get('members'):
                for each in have:
                    if each['members']:
                        if each['members'][0]['member'] == each_interface['member']:
                            break
                        else:
                            kwargs = {'want': interface, 'have': each}
                            commands.extend(Lag_interfaces.clear_interface(**kwargs))
                            continue
                    else:
                        # We didn't find a matching desired state, which means we can
                        # pretend we recieved an empty desired state.
                        kwargs = {'want': interface, 'have': each}
                        commands.extend(Lag_interfaces.clear_interface(**kwargs))
                        continue
                kwargs = {'want': interface, 'have': each}
                commands.extend(Lag_interfaces.clear_interface(**kwargs))
                kwargs = {'want': interface, 'have': each, 'commands': commands, 'module': module}
                commands.extend(Lag_interfaces.set_interface(**kwargs))
        # Remove the duplicate interface call
        commands = Lag_interfaces._remove_duplicate_interface(commands)

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
            for each_interface in interface.get('members'):
                for each in have:
                    if each['members']:
                        if each['members'][0]['member'] == each_interface['member']:
                            break
                    else:
                        if each.get('name') == each_interface['member']:
                            break
                else:
                    continue
                kwargs = {'want': interface, 'have': each, 'module': module}
                commands.extend(Lag_interfaces.set_interface(**kwargs))

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

        if want:
            for interface in want:
                for each in have:
                    if each.get('name') == interface['name']:
                        break
                else:
                    continue
                kwargs = {'want': interface, 'have': each, 'state': state}
                commands.extend(Lag_interfaces.clear_interface(**kwargs))
        else:
            for each in have:
                kwargs = {'want': {}, 'have': each, 'state': state}
                commands.extend(Lag_interfaces.clear_interface(**kwargs))

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
        if cmd not in commands:
            commands.append(cmd)

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
        channel_name_diff = False
        want = kwargs['want']
        have = kwargs['have']
        module = kwargs['module']
        if have['members']:
            interface = 'interface ' + have['members'][0]['member']
        else:
            interface = 'interface ' + have['name']
        member_diff = {}
        want_each_member = {}

        # To check if channel-group differs in want n have
        if have.get('name') != want.get('name'):
            channel_name_diff = True

        # Create Set for want and have field for diff comparison
        want_members = set(tuple({k: v for k, v in iteritems(member) if v is not None}.items())
                           for member in want.get("members") or [])
        if have['members']:
            have_member = set(tuple({k:v for k, v in iteritems(have['members'][0]) if v is not None}.items()))
        else:
            have_member = set(tuple({k:v for k, v in iteritems(have) if v}.items()))

        # Get the diff between want and have members
        for each_member in want_members:
            if dict(each_member)['member'] == dict(have_member).get('member'):
                want_each_member = each_member
                if have_member:
                    member_diff = dict(set(each_member) - have_member)
                    break
                else:
                    member_diff = dict(set(each_member))
                    break
            elif dict(each_member)['member'] == dict(have_member).get('name'):
                want_each_member = each_member
        # To get the diff channel mode n link config from computed diff
        mode = dict(member_diff).get('mode')
        link = dict(member_diff).get('link')
        # To get the channel-group ID from the interface Port-Channel
        channel_name = re.search('(\d+)', want.get('name'))
        if channel_name:
            channel_id = channel_name.group()
        else:
            module.fail_json(msg="Lag Interface Name is not correct!")
        # Compare the value and set the commands
        if mode:
            cmd = 'channel-group {} mode {}'.format(channel_id, mode)
            Lag_interfaces._add_command_to_interface(interface, cmd, commands)
        elif link:
            cmd = 'channel-group {} link {}'.format(channel_id, link)
            Lag_interfaces._add_command_to_interface(interface, cmd, commands)
        elif channel_name_diff and not member_diff:
            # In Merge case if want n have channel ID differs and channel mode config is kept same
            if want_each_member:
                final_dict = dict(want_each_member)
            else:
                final_dict = dict(have_member)
            mode = final_dict.get('mode')
            link = final_dict.get('link')
            if mode:
                cmd = 'channel-group {} mode {}'.format(channel_id, mode)
                Lag_interfaces._add_command_to_interface(interface, cmd, commands)
            elif link:
                cmd = 'channel-group {} link {}'.format(channel_id, link)
                Lag_interfaces._add_command_to_interface(interface, cmd, commands)

        return commands

    @staticmethod
    def clear_interface(**kwargs):
        # Delete the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        state = kwargs['state'] if kwargs.get('state') else ''

        if have['members']:
            interface = 'interface ' + have['members'][0]['member']
            if have.get('name') and (have.get('name') != want.get('name') or state == 'deleted'):
                Lag_interfaces._remove_command_from_interface(interface, 'channel-group', commands)

        return commands
