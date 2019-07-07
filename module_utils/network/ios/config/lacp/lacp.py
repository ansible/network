#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_lacp class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.six import iteritems

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts


class Lacp(ConfigBase):
    """
    The ios_lacp class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'interfaces',
    ]

    def __init__(self, module):
        super(Lacp, self).__init__(module)

    def get_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        interfaces_facts = facts['ansible_network_resources'].get('lacp')
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
        if state == 'deleted':
            kwargs = {'want': want, 'have': have, 'state': state}
            commands = self._state_deleted(**kwargs)
        elif state == 'merged':
            kwargs = {'want': want, 'have': have, 'state': state}
            commands = self._state_merged(**kwargs)
        elif state == 'replaced':
            kwargs = {'want': want, 'have': have, 'state': state}
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
        state = kwargs['state']

        for w, h in zip(want, have):
            kwargs = {'want': w, 'have': h, 'state': state}
            commands.extend(Lacp.clear_interface(**kwargs))
            kwargs = {'want': w, 'have': h, 'state': state}
            commands.extend(Lacp.set_interface(**kwargs))

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
        state = kwargs['state']

        for w, h in zip(want, have):
            kwargs = {'want': w, 'have': h, 'state': state}
        commands.extend(Lacp.set_interface(**kwargs))

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

        for w, h in zip(want, have):
            kwargs = {'want': w, 'have': h, 'state': state}
        commands.extend(Lacp.clear_interface(**kwargs))

        return commands

    @staticmethod
    def _remove_command_from_interface(cmd, commands):
        commands.append('no %s' % cmd)
        return commands

    @staticmethod
    def _add_command_to_interface(cmd, commands):
        if cmd not in commands:
            commands.append(cmd)

    @staticmethod
    def set_interface(**kwargs):
        # Set the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']

        want_dict = set(tuple({k: v for k, v in iteritems(want) if v is not None}.items()))
        have_dict = set(tuple({k: v for k, v in iteritems(have) if v is not None}.items()))
        diff = want_dict - have_dict

        if diff:
            cmd = 'lacp system-priority {}'.format(dict(diff).get('system_priority'))
            Lacp._add_command_to_interface(cmd, commands)

        return commands

    @staticmethod
    def clear_interface(**kwargs):
        # Delete the interface config based on the want and have config
        commands = []
        have = kwargs['have']
        state = kwargs['state']

        if have.get('system_priority') and have.get('system_priority') != 32768\
                and state == 'deleted' or state == 'replaced':
            cmd = 'lacp system-priority'
            Lacp._remove_command_from_interface(cmd, commands)

        return commands
