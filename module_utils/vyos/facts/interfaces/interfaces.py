#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from copy import deepcopy
from ansible.module_utils. \
     vyos.facts.base import FactsBase
from re import findall, M


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
        if module: #just for linting purposes
            pass
        if connection:  #just for linting purposes
            pass

        if not data:
            data = connection.get_config()

        objs = []

        interface_names = findall(r'^set interfaces ethernet (\S+)', data, M)
        if interface_names:
            for interface in set(interface_names):
                intf_regex = r' %s .+$' % interface
                cfg = findall(intf_regex, data, M)
                cfg = '\n'.join(cfg)
                obj = self.render_config(self.generated_spec, cfg)
                obj['name'] = interface
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
        if conf:
            pass

        config = deepcopy(spec)

        # populate the facts from the configuration
        attribs = ['description','speed', 'mtu', 'duplex']

        for x in attribs:
            config[x] = self.parse_conf_arg(conf, x)
        if '\'disable\'' in conf:
            config['enable'] = False
        else:
            config['enable'] = True

        return self.generate_final_config(config)
