#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos l2_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import re

from copy import deepcopy
from ansible.module_utils. \
     nxos.facts.base import FactsBase
from ansible.module_utils.nxos.utils.utils \
    import get_interface_type, normalize_interface, vlan_range_to_list

class L2_interfacesFacts(FactsBase):
    """ The nxos l2_interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for l2_interfaces

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

        facts = {}
        if objs:
            facts['l2_interfaces'] = objs

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
        # populate the facts from the configuration

        match = re.search(r'^(\S+)', conf)
        intf = match.group(1)
        if get_interface_type(intf) == 'unknown':
            return {}
        config['name'] = normalize_interface(intf)
        vlan = self.parse_conf_arg(conf, 'switchport access vlan')
        access_vlan = int(vlan) if vlan else None
        config['access'] = {'vlan': access_vlan}

        config['trunk'] = {}
        allowed_vlans = self.parse_conf_arg(conf, 'switchport trunk allowed vlan')
        config['trunk'].update({'allowed_vlans': allowed_vlans})

        native_vlan = self.parse_conf_arg(conf, 'switchport trunk native vlan')
        if native_vlan:
            native_vlan = int(native_vlan)
        config['trunk'].update({'native_vlan': native_vlan})

        return self.generate_final_config(config)
