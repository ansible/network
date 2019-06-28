#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, dict_diff
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.vyos.facts.facts import Facts
from ansible.module_utils.network. \
    vyos.utils.utils import search_obj_in_list, get_interface_type


class Interfaces(ConfigBase):
    """
    The vyos_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'interfaces'
    ]

    # NOTE: Don't change the ordering of params list
    #       The last two items are used for VIFs.
    params = ['speed', 'duplex', 'description', 'mtu']
    set_cmd = 'set interfaces '
    del_cmd = 'delete interfaces '

    def __init__(self, module):
        super(Interfaces, self).__init__(module)

    def get_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset,
                                                         self.gather_network_resources)
        interfaces_facts = facts['ansible_network_resources'].get('interfaces')
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
            if self._module.check_mode:
                resp = self._connection.edit_config(commands, commit=False)
            else:
                resp = self._connection.edit_config(commands)
            result['changed'] = True

        result['commands'] = commands

        if self._module._diff:
            result['diff'] = resp['diff'] if result['changed'] else None

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
        commands = []
        state = self._module.params['state']
        if state == 'overridden':
            commands.extend(Interfaces._state_overridden(want=want, have=have))
        else:
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have)
                if state == 'deleted':
                    commands.extend(
                        Interfaces._state_deleted(
                            want_intf=item, have_intf=obj_in_have
                        )
                    )

                elif state == 'merged':
                    commands.extend(
                        Interfaces._state_merged(
                            want_intf=item, have_intf=obj_in_have
                        )
                    )

                elif state == 'replaced':
                    commands.extend(
                        Interfaces._state_replaced(
                            want_intf=item, have_intf=obj_in_have
                        )
                    )

        return commands

    @staticmethod
    def _state_replaced(**kwargs):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want_intf = kwargs['want_intf']
        have_intf = kwargs['have_intf']

        if have_intf:
            commands.extend(
                Interfaces._render_del_commands(
                    want_element={'intf': want_intf},
                    have_element={'intf': have_intf}
                )
            )

            have_vifs = have_intf.get('vifs')
            want_vifs = want_intf['vifs']

            if have_vifs:
                for have_vif in have_vifs:
                    want_vif = {}
                    if want_vifs:
                        want_vif = search_obj_in_list(
                            have_vif['vlan_id'], want_vifs, key='vlan_id'
                        )
                        if not want_vif:
                            want_vif = {}

                    commands.extend(
                        Interfaces._render_del_commands(
                            want_element={
                                'intf': want_intf,
                                'vif': want_vif
                            },
                            have_element={
                                'intf': have_intf,
                                'vif': have_vif
                            }
                        )
                    )

        commands.extend(
            Interfaces._state_merged(
                want_intf=want_intf,
                have_intf=have_intf
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
        want_intfs = kwargs['want']
        have_intfs = kwargs['have']

        for have_intf in have_intfs:
            intf_name = have_intf['name']
            intf_in_want = search_obj_in_list(intf_name, want_intfs)
            if not intf_in_want:
                commands.extend(Interfaces._purge_attribs(intf=have_intf))

        for intf in want_intfs:
            name = intf['name']
            intf_in_have = search_obj_in_list(name, have_intfs)
            commands.extend(
                Interfaces._state_replaced(
                    want_intf=intf,
                    have_intf=intf_in_have
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
        want_intf = kwargs['want_intf']
        have_intf = kwargs['have_intf']

        if have_intf:
            commands.extend(
                Interfaces._render_updates(
                    want_element={'intf': want_intf},
                    have_element={'intf': have_intf}
                )
            )

            have_vifs = have_intf.get('vifs')
            want_vifs = want_intf['vifs']

            if want_vifs:
                for want_vif in want_vifs:
                    have_vif = {}
                    if have_vifs:
                        have_vif = search_obj_in_list(
                            want_vif['vlan_id'], have_vifs, key='vlan_id'
                        )
                        if not have_vif:
                            have_vif = {}

                    if have_vif:
                        commands.extend(
                            Interfaces._render_updates(
                                want_element={
                                    'intf': want_intf,
                                    'vif': want_vif
                                },
                                have_element={
                                    'intf': have_intf,
                                    'vif': have_vif
                                }
                            )
                        )
                    else:
                        commands.extend(
                            Interfaces._render_set_commands(
                                want_element={
                                    'intf': want_intf,
                                    'vif': want_vif
                                }
                            )
                        )
        else:
            commands.extend(
                Interfaces._render_set_commands(
                    want_element={
                        'intf': want_intf
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

        have_intf = kwargs['have_intf']
        if have_intf:
            commands.extend(Interfaces._purge_attribs(intf=have_intf))

        return commands

    @staticmethod
    def _render_updates(**kwargs):
        commands = []
        want_element = kwargs['want_element']
        have_element = kwargs['have_element']

        intf_name = have_element['intf']['name']

        if have_element.get('vif'):
            isvif = True
            del_cmd = Interfaces.del_cmd + get_interface_type(intf_name) + \
                ' ' + intf_name + ' vif ' + have_element['vif']['vlan_id']
            set_cmd = Interfaces.set_cmd + get_interface_type(intf_name) + \
                ' ' + intf_name + ' vif ' + have_element['vif']['vlan_id']
            have_item = have_element['vif']
            want_item = want_element['vif']
        else:
            isvif = False
            set_cmd = Interfaces.set_cmd + get_interface_type(intf_name) + ' ' + intf_name
            del_cmd = Interfaces.del_cmd + get_interface_type(intf_name) + ' ' + intf_name
            have_item = have_element['intf']
            want_item = want_element['intf']

        updates = dict_diff(have_item, want_item)
        if updates:
            if not isvif:
                try:
                    del updates['vifs']
                except BaseException:
                    pass
            for key, value in iteritems(updates):
                if key == 'enable':
                    if value:
                        commands.append(del_cmd + ' disable')
                    else:
                        commands.append(set_cmd + ' disable')
                elif value:
                    commands.append(
                        set_cmd + ' ' + key + " '" + str(value) + "'"
                    )

        return commands

    @staticmethod
    def _render_set_commands(**kwargs):
        commands = []
        want_element = kwargs['want_element']
        intf_name = want_element['intf']['name']
        set_cmd = Interfaces.set_cmd + get_interface_type(intf_name) + ' ' + intf_name

        if want_element.get('vif'):
            set_cmd = set_cmd + ' vif ' + want_element['vif']['vlan_id']
            params = Interfaces.params[-2:]
            want_item = want_element['vif']

        else:
            params = Interfaces.params
            want_item = want_element['intf']

        commands.append(set_cmd)
        for attrib in params:
            value = want_item[attrib]
            if value:
                commands.append(
                    set_cmd + ' ' + attrib + " '" + str(value) + "'"
                )
        if not want_item['enable']:
            commands.append(set_cmd + ' disable')

        return commands

    @staticmethod
    def _render_del_commands(**kwargs):
        commands = []
        want_element = kwargs['want_element']
        have_element = kwargs['have_element']
        have_intf_name = have_element['intf']['name']
        del_cmd = Interfaces.del_cmd + get_interface_type(have_intf_name) + ' ' + have_intf_name

        if have_element.get('vif'):
            del_cmd = del_cmd + ' vif ' + \
                have_element['vif']['vlan_id'].strip("'")
            params = Interfaces.params[-2:]
            have_item = have_element['vif']
            want_item = want_element['vif']
        else:
            params = Interfaces.params
            have_item = have_element['intf']
            want_item = want_element['intf']

        for attrib in params:
            if have_item.get(attrib) and not want_item.get(attrib):
                commands.append(del_cmd + ' ' + attrib)

        return commands

    @staticmethod
    def _purge_attribs(**kwargs):
        commands = []
        intf = kwargs['intf']
        intf_name = intf['name']
        del_intf = Interfaces.del_cmd + get_interface_type(intf_name) + ' ' + intf_name

        for item in Interfaces.params:
            if intf.get(item):
                commands.append(del_intf + ' ' + item)
            if not intf['enable']:
                commands.append(del_intf + ' disable')

        if intf.get('vifs'):
            for vif in intf['vifs']:
                for attrib in Interfaces.params[-2:]:
                    if vif.get(attrib):
                        commands.append(del_intf + ' vif ' + vif['vlan_id'] + ' ' + attrib)
                if not vif['enable']:
                    commands.append(del_intf + ' vif ' + vif['vlan_id'] + ' disable')

        return commands
