#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The exos_lldp_global class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.exos.facts.facts import Facts


class Lldp_global(ConfigBase):
    """
    The exos_lldp_global class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_global',
    ]

    LLDP_DEFAULT_INTERVAL = 30
    LLDP_DEFAULT_TLV_SUPPRESSED = ['SYSTEM_CAPABILITIES', 'PORT_DESCRIPTION', 'MANAGEMENT_ADDRESS']

    def __init__(self, module):
        super(Lldp_global, self).__init__(module)

    def get_lldp_global_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lldp_global_facts = facts['ansible_network_resources'].get('lldp_global')
        if not lldp_global_facts:
            return {}
        return lldp_global_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        requests = list()

        existing_lldp_global_facts = self.get_lldp_global_facts()
        requests.extend(self.set_config(existing_lldp_global_facts))
        if requests:
            if not self._module.check_mode:
                self._connection.send_requests(requests)
            result['changed'] = True
        result['requests'] = requests

        changed_lldp_global_facts = self.get_lldp_global_facts()

        result['before'] = existing_lldp_global_facts
        if result['changed']:
            result['after'] = changed_lldp_global_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lldp_global_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lldp_global_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params['state']

        if state == 'deleted':
            requests = self._state_deleted(want, have)
        elif state == 'merged':
            requests = self._state_merged(want, have)
        elif state == 'replaced':
            requests = self._state_replaced(want, have)

        return requests

    def _state_replaced(self, want, have):
        """ The request generator when state is replaced

        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        requests = []
        requests.extend(self._state_deleted(want, have))
        requests.extend(self._state_merged(want, have))
        return requests

    def _state_merged(self, want, have):
        """ The request generator when state is merged

        :rtype: A list
        :returns: the requests necessary to merge the provided into
                  the current configuration
        """
        request = {
            'body': {"openconfig_lldp:config": {}},
            'method': 'PATCH',
            'path': '/rest/restconf/data/openconfig-lldp:lldp/config'
        }
        if want.get('interval'):
            if want['interval'] != have['interval']:
                request['body']['openconfig_lldp:config']['hello-timer'] = want['interval']
        if want.get('tlv-select'):
            if want['tlv-select'] != have['tlv-select']:
                request['body']['openconfig_lldp:config']['suppress-tlv-advertisement'] = [
                    tlv.key().upper() for tlv in want['tlv-select'] if tlv.value() is False]
        return request

    def _state_deleted(self, want, have):
        """ The request generator when state is deleted

        :rtype: A list
        :returns: the requests necessary to remove the current configuration
                  of the provided objects
        """
        request = {
            'body': {"openconfig_lldp:config": {}},
            'method': 'PUT',
            'path': '/rest/restconf/data/openconfig-lldp:lldp/config'
        }
        request['body']['openconfig_lldp:config']['hello-timer'] = self.LLDP_DEFAULT_INTERVAL
        request['body']['openconfig_lldp:config']['suppress-tlv-advertisement'] = [
            tlv for tlv in self.LLDP_DEFAULT_TLV_SUPPRESSED]
        return request
