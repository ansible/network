#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

import re
from copy import deepcopy

from ansible.module_utils.ios.facts.base import FactsBase
from ansible.module_utils.ios.utils.utils import get_interface_type, normalize_interface


class L3_interfacesFacts(FactsBase):
    """ The ios l3 interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for l3 interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []

        if not data:
            data = connection.get('show running-config | section ^interface')
        # operate on a collection of resource x
        config = data.split('interface ')
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)
        facts = {}

        if objs:
            facts['l3_interfaces'] = objs
        self.ansible_facts['ansible_network_resources'].update(facts)
        return self.ansible_facts

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys from spec for null values
        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        match = re.search(r'^(\S+)', conf)
        intf = match.group(1)

        if get_interface_type(intf) == 'unknown':
            return {}
        # populate the facts from the configuration
        config['name'] = normalize_interface(intf)

        ipv4 = []
        ipv4_all = re.findall(r"ip address (\S+.*)", conf)
        for each in ipv4_all:
            each_ipv4 = dict()
            if 'secondary' not in each and 'dhcp' not in each:
                each_ipv4['address'] = each
                each_ipv4['secondary'] = False
            elif 'secondary' in each:
                each_ipv4['secondary'] = True
                each_ipv4['address'] = each.split(' secondary')[0]
            elif 'dhcp' in each:
                each_ipv4['address'] = 'dhcp'
                if 'hostname' in each and 'client-id' in each:
                    each_ipv4["dhcp_hostname"] = each.split(' hostname ')[-1]
                    each_ipv4['dhcp_client'] = each.split(' hostname ')[0].split('/')[-1]
                if 'client-id' in each and not each_ipv4['dhcp_client']:
                    each_ipv4['dhcp_client'] = each.split('/')[-1]
                if 'hostname' in each and not each_ipv4["dhcp_hostname"]:
                    each_ipv4["dhcp_hostname"] = each.split(' hostname ')[-1]

            ipv4.append(each_ipv4)
        config['ipv4'] = ipv4

        # Get the configured IPV6 details
        ipv6 = []
        ipv6_all = re.findall(r"ipv6 address (\S+)", conf)
        for each in ipv6_all:
            each_ipv6 = dict()
            if 'autoconfig' in each:
                each_ipv6['autoconfig'] = True
            if 'dhcp' in each:
                each_ipv6['dhcp'] = True
            each_ipv6['address'] = each.lower()
            ipv6.append(each_ipv6)
        config['ipv6'] = ipv6

        encapsulation = re.search(r"encapsulation (\S+)", conf)
        if encapsulation:
            config['encapsulation'] = True

        return self.generate_final_config(config)
