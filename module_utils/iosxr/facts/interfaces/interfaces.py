#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

import re
from copy import deepcopy

from ansible.module_utils.iosxr.facts.base import FactsBase
from ansible.module_utils.iosxr.utils.utils import get_interface_type, normalize_interface


class InterfacesFacts(FactsBase):
    """ The iosxr interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for interfaces

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
            facts['interfaces'] = objs
        self.ansible_facts['net_configuration'].update(facts)
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
        if match.group(1).lower() == "preconfigure":
            match = re.search(r'^(\S+ \S+)', conf)
        intf = match.group(1)
        if get_interface_type(intf) == 'unknown':
            return {}
        # populate the facts from the configuration
        config['name'] = normalize_interface(intf)
        config['description'] = self.parse_conf_arg(conf, 'description')
        config['speed'] = self.parse_conf_arg(conf, 'speed')
        config['mtu'] = self.parse_conf_arg(conf, 'mtu')
        config['duplex'] = self.parse_conf_arg(conf, 'duplex')
        enabled = self.parse_conf_cmd_arg(conf, 'shutdown', False)
        config['enabled'] = enabled if enabled is not None else config['enabled']

        return self.generate_final_config(config)
