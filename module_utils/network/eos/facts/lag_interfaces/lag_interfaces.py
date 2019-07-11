#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos lag_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import re
from copy import deepcopy
from ansible.module_utils.network.eos.facts.base import FactsBase


class Lag_interfacesFacts(FactsBase):
    """ The eos lag_interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for lag_interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get('show running-config | section ^interface')

        # split the config into instances of the resource
        resource_delim = 'interface'
        find_pattern = r'(?:^|\n)%s.*?(?=(?:^|\n)%s|$)' % (resource_delim,
                                                           resource_delim)
        resources = [p.strip() for p in re.findall(find_pattern,
                                                   data,
                                                   re.DOTALL)]

        objs = {}
        for resource in resources:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    group_name = obj['name']
                    if group_name in objs:
                        objs[group_name]['members'].extend(obj['members'])
                    else:
                        objs[group_name] = obj
        facts = {}
        if objs:
            facts['lag_interfaces'] = list(objs.values())
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

        interface = {'member': self.parse_conf_arg(conf, 'interface')}

        match = re.match(r'.*channel-group (\d+) mode (\S+)', conf, re.MULTILINE | re.DOTALL)
        if match:
            config['name'], interface['mode'] = match.groups()
            config['members'] = [interface]

        return self.generate_final_config(config)
