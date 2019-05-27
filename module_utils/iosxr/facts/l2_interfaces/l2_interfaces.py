#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr l2 interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

import re
from copy import deepcopy

from ansible.module_utils.iosxr.facts.base import FactsBase
from ansible.module_utils.iosxr.utils.utils import get_interface_type, normalize_interface


class L2_interfacesFacts(FactsBase):
    """ The iosxr l2 interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for l2_interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if module: #just for linting purposes
            pass
        if connection:  #just for linting purposes
            pass
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
        match = re.search(r'^(\S+)', conf)

        if len(match.group().split('.')) > 1:
            sub_match = re.search(r'^(\S+ \S+)', conf)
            if sub_match:
                intf = sub_match.group()
                config['name'] = intf
            else:
                intf = match.group(1)
                config['name'] = intf
        else:
            intf = match.group(1)
            if get_interface_type(intf) == 'unknown':
                return {}
            # populate the facts from the configuration
            config['name'] = normalize_interface(intf)
        native_vlan = re.search(r"dot1q native vlan (\d+)", conf)
        if native_vlan:
            config["native_vlan"] = {"vlan": int(native_vlan.group(1))}
        if 'l2transport' in config['name']:
            config['q_vlan'] = self.parse_conf_arg(conf, 'dot1q vlan')
        else:
            config['q_vlan'] = self.parse_conf_arg(conf, 'encapsulation dot1q')

        if self.parse_conf_arg(conf, 'propagate'):
            config['propagate'] = True
        config['l2protocol_cdp'] = self.parse_conf_arg(conf, 'l2protocol cdp')
        config['l2protocol_pvst'] = self.parse_conf_arg(conf, 'l2protocol pvst')
        config['l2protocol_stp'] = self.parse_conf_arg(conf, 'l2protocol stp')
        config['l2protocol_vtp'] = self.parse_conf_arg(conf, 'l2protocol vtp')
        if config.get('propagate') or config.get('l2protocol_cdp') or config.get('l2protocol_pvst') or\
            config.get('l2protocol_stp') or config.get('l2protocol_vtp'):
            config['l2transport'] = True

        return self.generate_final_config(config)