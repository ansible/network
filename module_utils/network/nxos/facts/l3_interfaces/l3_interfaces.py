#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos l3_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import re
from copy import deepcopy
from ansible.module_utils.network. \
    nxos.facts.base import FactsBase
from ansible.module_utils.network.nxos.utils.utils \
    import get_interface_type, normalize_interface, validate_ipv4_addr, validate_ipv6_addr


class L3_interfacesFacts(FactsBase):
    """ The nxos l3_interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for l3_interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []
        if not data:
            data = connection.get('show running-config | section ^interface')
        config = data.split('interface ')
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj and len(obj.keys()) > 1:
                    objs.append(obj)

        self.ansible_facts['ansible_network_resources'].pop('l3_interfaces', None)       
        facts = {}
        if objs:
            facts['l3_interfaces'] = objs

        self.ansible_facts['ansible_network_resources'].update(facts)
        return self.ansible_facts

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

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
        config['name'] = normalize_interface(intf)

        ipv4_match = re.compile(r'\n  ip address (.*)')
        matches = ipv4_match.findall(conf)
        if matches:
            if validate_ipv4_addr(matches[0]):
                config['ipv4'] = []
                for m in matches:
                    ipv4_conf = m.split()
                    addr = ipv4_conf[0]
                    ipv4_addr = addr if validate_ipv4_addr(addr) else None
                    if ipv4_addr:
                        config_dict = {'address': ipv4_addr}
                        if len(ipv4_conf) > 1:
                            d = ipv4_conf[1]
                            if d == 'secondary':
                                config_dict.update({'secondary': True})
                                if len(ipv4_conf) == 4:
                                    if ipv4_conf[2] == 'tag':
                                        config_dict.update({'tag': int(ipv4_conf[-1])})
                            elif d == 'tag':
                                config_dict.update({'tag': int(ipv4_conf[-1])})
                        config['ipv4'].append(config_dict)

        ipv6_match = re.compile(r'\n  ipv6 address (.*)')
        matches = ipv6_match.findall(conf)
        if matches:
            if validate_ipv6_addr(matches[0]):
                config['ipv6'] = []
                for m in matches:
                    ipv6_conf = m.split()
                    addr = ipv6_conf[0]
                    ipv6_addr = addr if validate_ipv6_addr(addr) else None
                    if ipv6_addr:
                        config_dict = {'address': ipv6_addr}
                        if len(ipv6_conf) > 1:
                            d = ipv6_conf[1]
                            if d == 'tag':
                                config_dict.update({'tag': int(ipv6_conf[-1])})
                        config['ipv6'].append(config_dict)

        return self.generate_final_config(config)
