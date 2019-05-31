#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from re import findall, M
from ansible.module_utils.network. \
    vyos.facts.base import FactsBase


class InterfacesFacts(FactsBase):
    """ The vyos interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if module:  # just for linting purposes, remove
            pass
        if connection:  # just for linting purposes, remove
            pass

        if not data:
            data = connection.get_config()

        objs = []
        interface_names = findall(r'^set interfaces ethernet (\S+)', data, M)
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
            facts['interfaces'] = objs
        self.ansible_facts['ansible_network_resources'].update(facts)
        return self.ansible_facts

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """

        vif_conf = '\n'.join(filter(lambda x: ('vif' in x), conf))
        eth_conf = '\n'.join(filter(lambda x: ('vif' not in x), conf))
        config = self.parse_attribs(
            ['description', 'speed', 'mtu', 'duplex'], eth_conf)
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
                obj = self.parse_attribs(['description', 'mtu'], cfg)
                obj['vlan_id'] = vif
                if obj:
                    vifs_list.append(obj)
        return vifs_list

    def parse_attribs(self, attribs, conf):
        config = {}
        for item in attribs:
            value = self.parse_conf_arg(conf, item)
            if value and item == 'mtu':
                config[item] = int(value)
            else:
                config[item] = value
        if 'disable' in conf:
            config['enable'] = False
        else:
            config['enable'] = True

        return self.generate_final_config(config)
