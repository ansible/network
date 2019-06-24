#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos lag_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import re
from copy import deepcopy
from ansible.module_utils.network. \
    nxos.facts.base import FactsBase
from ansible.module_utils.network.nxos.utils.utils \
    import get_interface_type, normalize_interface


class Lag_interfacesFacts(FactsBase):
    """ The nxos lag_interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for lag_interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []
        if not data:
            data = connection.get('show running-config | include channel-group')
        config = re.split('(\n  |)channel-group ', data)
        config = list(dict.fromkeys(config))
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf, connection)
                if obj and len(obj.keys()) > 1:
                    objs.append(obj)

        self.ansible_facts['ansible_network_resources'].pop('lag_interfaces', None) 
        facts = {}
        if objs:
            facts['lag_interfaces'] = objs

        self.ansible_facts['ansible_network_resources'].update(facts)
        return self.ansible_facts

    def get_members(self, id, connection):
        """
        Returns members associated with a channel-group
        
        :param name: The channel group
        :rtype: list
        :returns: Members
        """
        members = []
        data = connection.get('show port-channel summary')
        match = re.search(r'{} (.+)(|\n)'.format(id), data)
        if match:
            interfaces = re.search('Eth\d(.+)$', match.group())
            if interfaces:
                for i in interfaces.group().split():
                    if get_interface_type(i[:-3]) != 'unknown':
                        members.append(normalize_interface(i[:-3]))

        return members


    def render_config(self, spec, conf, connection):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        match = re.search(r'(\d+)( |)(force )?(mode \S+)?', conf, re.M)
        if match:
            matches = match.groups()
            config['id'] = int(matches[0])
            config['members'] = []
            members = self.get_members(config['id'], connection)
            if members:
                for m in members:
                    m_dict = {}
                    if matches[2]:
                        m_dict['force'] = matches[2]
                    if matches[3]:
                        m_dict['mode'] = matches[3][5:]
                    m_dict['member'] = m
                    config['members'].append(m_dict)
        else:
            config = {}
        return self.generate_final_config(config)
