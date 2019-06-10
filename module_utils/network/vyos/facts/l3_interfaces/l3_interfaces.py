#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos l3_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import ipaddress
from ansible.module_utils.six import iteritems
from re import findall, M
from ansible.module_utils.network. \
    vyos.facts.base import FactsBase


class L3_interfacesFacts(FactsBase):
    """ The vyos l3_interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for l3_interfaces

        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if module:  # just for linting purposes
            pass
        if connection:  # just for linting purposes
            pass

        if not data:
            data = connection.get_config()

        # operate on a collection of resource x
        objs = []
        interface_names = findall(r'set interfaces (?:ethernet|bonding) (\S+)', data, M)
        if interface_names:
            for interface in set(interface_names):
                intf_regex = r' %s .+$' % interface
                cfg = findall(intf_regex, data, M)
                obj = self.render_config(cfg)
                obj['name'] = interface
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            facts['l3_interfaces'] = objs
        self.ansible_facts['ansible_network_resources'].update(facts)
        return self.ansible_facts

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        vif_conf = '\n'.join(filter(lambda x: ('vif' in x), conf))
        eth_conf = '\n'.join(filter(lambda x: ('vif' not in x), conf))
        config = self.parse_attribs(eth_conf)
        config['vifs'] = self.parse_vifs(vif_conf)

        return self.generate_final_config(config)

    def parse_vifs(self, conf):
        vif_names = findall(r'vif (\S+)', conf, M)
        vifs_list = None
        if vif_names:
            vifs_list = []
            for vif in set(vif_names):
                vif_regex = r' %s .+$' % vif
                cfg = '\n'.join(findall(vif_regex, conf, M))
                obj = self.parse_attribs(cfg)
                obj['vlan_id'] = vif
                if obj:
                    vifs_list.append(obj)

        return vifs_list

    def parse_attribs(self, conf):
        config = {}
        ipaddrs = findall(r'address (\S+)', conf, M)
        config['ipv4'] = []
        config['ipv6'] = []

        for item in ipaddrs:
            item = item.strip("'")
            if item == 'dhcp':
                config['ipv4'].append({'address': item})
            elif item == 'dhcpv6':
                config['ipv6'].append({'address': item})
            else:
                ip_version = ipaddress.ip_address(item.split("/")[0]).version
                if ip_version == 4:
                    config['ipv4'].append({'address': item})
                else:
                    config['ipv6'].append({'address': item})

        for key, value in iteritems(config):
            if value == []:
                config[key] = None

        return self.generate_final_config(config)
