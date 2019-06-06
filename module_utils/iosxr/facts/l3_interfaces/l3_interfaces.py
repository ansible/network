#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr l3 interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

import re
from copy import deepcopy

from ansible.module_utils.iosxr.facts.base import FactsBase
from ansible.module_utils.iosxr.utils.utils import get_interface_type, normalize_interface


class L3_interfacesFacts(FactsBase):
    """ The iosxr l3 interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []

        if not data:
            data = connection.get('show running-config interface')
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

        # Get the configured IPV4 details
        ipv4 = re.findall(r"ipv4 address (\S+.*)", conf)
        for each in ipv4:
            if 'secondary' in each:
                config['secondary'] = True
                config['secondary_ipv4'] = each.split(' secondary')[0]
            else:
                config["ipv4"] = each

        # Get the configured IPV6 details
        ipv6 = re.findall(r"ipv6 address (\S+)", conf)
        for each in ipv6:
            config["ipv6"] = each

        # To verify if L2transport is configured on the interface
        l2transport = False
        interface_name = re.search(r'^(\S+) (\S.*)', conf)
        if interface_name:
            if 'l2transport' in interface_name.group():
                l2transport = True
        elif re.search(r"l2transport", conf):
            l2transport = True
        if l2transport:
            config['l2transport'] = True

        return self.generate_final_config(config)
