#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_lldp class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, dict_diff
from ansible.module_utils.network.vyos.facts.facts import Facts
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.vyos.utils.utils import search_obj_in_list, \
    add_lldp_protocols, update_lldp_protocols, merge_two_dicts


class Lldp(ConfigBase):
    """
    The vyos_lldp class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp',
    ]

    params = ['enable', 'address', 'snmp', 'legacy_protocols']
    set_cmd = 'set service lldp '
    del_cmd = 'delete service lldp '

    def __init__(self, module):
        super(Lldp, self).__init__(module)

    def get_lldp_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset,
                                                         self.gather_network_resources)
        lldp_facts = facts['ansible_network_resources'].get('lldp')
        if not lldp_facts:
            return []
        return lldp_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_lldp_facts = self.get_lldp_facts()
        commands.extend(self.set_config(existing_lldp_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_lldp_facts = self.get_lldp_facts()

        result['before'] = existing_lldp_facts
        if result['changed']:
            result['after'] = changed_lldp_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lldp_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lldp_facts
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
        if state == 'deleted':
            commands.extend(self._state_deleted(have_lldp=have))
        elif state == 'merged':
            commands.extend(self._state_merged(want_lldp=want, have_lldp=have))
        elif state == 'replaced':
            commands.extend(self._state_replaced(want_lldp=want, have_lldp=have))
        return commands

    @staticmethod
    def _state_replaced(**kwargs):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        have_item = {}
        want_lldp = kwargs['want_lldp']
        have_lldp = kwargs['have_lldp']
        for item in have_lldp:
            have_item = merge_two_dicts(have_item, item)

        if have_item:
            commands.extend(
                Lldp._render_del_commands(
                    want_element={'lldp': want_lldp},
                    have_element={'lldp': have_item}
                )
            )
        commands.extend(
            Lldp._state_merged(
                want_lldp=want_lldp,
                have_lldp=have_lldp
            )
        )
        return commands

    @staticmethod
    def _state_overridden(**kwargs):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want_lldps = kwargs['want']
        have_lldps = kwargs['have']

        for have_item in have_lldps:
            lldp_in_want = search_obj_in_list(have_item, want_lldps)
            if not lldp_in_want:
                commands.extend(
                    Lldp._purge_attribs(
                        lldp=have_item
                    )
                )

        for want_item in want_lldps:
            lldp_in_have = search_obj_in_list(want_item, have_lldps)
            commands.extend(
                Lldp._state_replaced(
                    want_lldp=want_item,
                    have_lldp=lldp_in_have
                )
            )
        return commands

    @staticmethod
    def _state_merged(**kwargs):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        have_item = {}
        want_lldp = kwargs['want_lldp']
        have_lldp = kwargs['have_lldp']
        for item in have_lldp:
            have_item = merge_two_dicts(have_item, item)

        commands.extend(
            Lldp._render_updates(
                want_element={'lldp': want_lldp},
                have_element={'lldp': have_item}
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
        have_item = {}
        have_lldp = kwargs['have_lldp']

        for item in have_lldp:
            have_item = merge_two_dicts(have_item, item)
        if have_item:
            commands.extend(Lldp._purge_attribs(lldp=have_item))
        return commands

    @staticmethod
    def _render_updates(**kwargs):
        commands = []
        want_element = kwargs['want_element']
        have_element = kwargs['have_element']

        have_item = have_element['lldp']
        want_item = want_element['lldp']

        updates = dict_diff(have_item, want_item)

        if updates:
            for key, value in iteritems(updates):
                if value:
                    if key == 'legacy_protocols':
                        commands.extend(add_lldp_protocols(want_item, have_item))
                    elif key == 'enable':
                        commands.append(Lldp.set_cmd)
                    elif key == 'address':
                        commands.append(
                            Lldp.set_cmd + 'management-address' + " '" + str(value) + "'"
                        )
                    elif key == 'snmp':
                        if value == 'disable':
                            commands.append(Lldp.del_cmd + key)
                        else:
                            commands.append(Lldp.set_cmd + key + ' ' + str(value))
        return commands

    @staticmethod
    def _purge_attribs(**kwargs):
        commands = []
        lldp = kwargs['lldp']
        for item in Lldp.params:
            if lldp.get(item):
                if item == 'legacy_protocols':
                    commands.append(Lldp.del_cmd + 'legacy-protocols')
                elif item == 'address':
                    commands.append(Lldp.del_cmd + 'management-address')
                elif item == 'snmp':
                    commands.append(Lldp.del_cmd + item)
        return commands

    @staticmethod
    def _render_del_commands(**kwargs):
        commands = []
        want_element = kwargs['want_element']
        have_element = kwargs['have_element']

        params = Lldp.params
        have_item = have_element['lldp']
        want_item = want_element['lldp']

        for attrib in params:
            if attrib == 'legacy_protocols':
                commands.extend(update_lldp_protocols(want_item, have_item))
            elif have_item.get(attrib) and not want_item.get(attrib):
                commands.append(Lldp.del_cmd + attrib)
        return commands
