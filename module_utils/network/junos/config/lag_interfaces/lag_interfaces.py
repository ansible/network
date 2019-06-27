#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos_lag_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, get_xml_conf_arg
from ansible.module_utils.network.junos.facts.facts import Facts
from ansible.module_utils.network.junos.junos import locked_config, load_config, commit_configuration, discard_changes, tostring
from ansible.module_utils.network.junos.utils import utils as junosutils


class Lag_interfaces(ConfigBase):
    """
    The junos_lag_interfaces class
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
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lag_interfaces_facts = facts['ansible_network_resources'].get('lag_interfaces')
        if not lag_interfaces_facts:
            return []
        return lag_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()

        existing_lag_interfaces_facts = self.get_lag_interfaces_facts()
        config_xmls = self.set_config(existing_lag_interfaces_facts)

        with locked_config(self._module):
            for config_xml in to_list(config_xmls):
                diff = load_config(self._module, config_xml, warnings)

            commit = not self._module.check_mode
            if diff:
                if commit:
                    commit_configuration(self._module)
                else:
                    discard_changes(self._module)
                result['changed'] = True

                if self._module._diff:
                    result['diff'] = {'prepared': diff}

        result['xml'] = config_xmls

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
        root = junosutils.build_root_xml_node('interfaces')
        state = self._module.params['state']
        if state == 'overridden':
            config_xmls = self._state_overridden(want, have)
        elif state == 'deleted':
            config_xmls = self._state_deleted(want, have)
        elif state == 'merged':
            config_xmls = self._state_merged(want, have)
        elif state == 'replaced':
            config_xmls = self._state_replaced(want, have)

        for xml in config_xmls:
            root.append(xml)

        return tostring(root)

    def _state_replaced(self, want, have):
        """ The xml configuration generator when state is replaced
        :rtype: A list
        :returns: the xml configuration necessary to migrate the current configuration
                  to the desired configuration
        """
        intf_xml = []
        intf_xml.extend(self._state_deleted(want, have))
        intf_xml.extend(self._state_merged(want, have))

        return intf_xml

    def _state_overridden(self, want, have):
        """ The xml configuration generator when state is overridden
        :rtype: A list
        :returns: the xml configuration necessary to migrate the current configuration
                  to the desired configuration
        """
        interface_xmls_obj = []
        # replace interface config with data in want
        interface_xmls_obj.extend(self._state_replaced(want, have))

        # delete interface config if interface in have not present in want
        delete_obj = []
        for have_obj in have:
            for want_obj in want:
                if have_obj['name'] == want_obj['name']:
                    break
            else:
                delete_obj.append(have_obj)

        interface_xmls_obj.extend(self._state_deleted(delete_obj, have))
        return interface_xmls_obj

    def _state_merged(self, want, have):
        """ The xml configuration generator when state is merged
         :rtype: A list
         :returns: the xml configuration necessary to merge the provided into
                   the current configuration
         """
        intf_xml = []

        for config in want:
            lag_intf_root = junosutils.build_root_xml_node('interface')
            junosutils.build_child_xml_node(lag_intf_root, 'name', config['name'])
            junosutils.build_child_xml_node(lag_intf_root, 'description', config['description'])

            if config['mode']:
                element = junosutils.build_subtree(lag_intf_root, 'aggregated-ether-options/lacp')
                junosutils.build_child_xml_node(element, config['mode'])
            intf_xml.append(lag_intf_root)

            members = config['members']
            for member in members:
                lag_member_intf_root = junosutils.build_root_xml_node('interface')
                junosutils.build_child_xml_node(lag_member_intf_root, 'name', member)
                element = junosutils.build_subtree(lag_member_intf_root, 'ether-options/ieee-802.3ad/bundle')
                element.text = config['name']
                intf_xml.append(lag_member_intf_root)

        return intf_xml

    def _state_deleted(self, want, have):
        """ The xml configuration generator when state is deleted
        :rtype: A list
        :returns: the xml configuration necessary to remove the current configuration
                  of the provided objects
        """
        intf_xml = []

        for config in want:
            lag_name = config['name']
            lag_intf_root = junosutils.build_root_xml_node('interface')
            junosutils.build_child_xml_node(lag_intf_root, 'name', lag_name)
            junosutils.build_child_xml_node(lag_intf_root, 'description', None, {'delete': 'delete'})

            element = junosutils.build_subtree(lag_intf_root, 'aggregated-ether-options/lacp')
            junosutils.build_child_xml_node(element, 'active', None, {'delete': 'delete'})
            junosutils.build_child_xml_node(element, 'passive', None, {'delete': 'delete'})
            intf_xml.append(lag_intf_root)

            # delete lag configuration from member interfaces
            for interface_obj in have:
                if lag_name == interface_obj['name']:
                    for member in interface_obj.get('members', []):
                        lag_member_intf_root = junosutils.build_root_xml_node('interface')
                        junosutils.build_child_xml_node(lag_member_intf_root, 'name', member)
                        element = junosutils.build_subtree(lag_member_intf_root, 'ether-options/ieee-802.3ad/bundle')
                        element.attrib.update({'delete': 'delete'})
                        intf_xml.append(lag_member_intf_root)

        return intf_xml
