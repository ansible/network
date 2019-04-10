#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from copy import deepcopy
from ansible.module_utils.eos.facts.base import FactsBase


class InterfacesFacts(FactsBase):
    """ The eos interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for interfaces

        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get('show running-config | section interface')

        # operate on a collection of resource x
        config = data.split('interface ')
        objs = []
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
        # populate the facts from the configuration
        config_lines = conf.split('\n')

        config['name'] = config_lines[0]
        for line in config_lines[1:]:
            line = line.strip()

            if line.startswith('description'):
                config['description'] = line.split(None, 1)[1].replace('"', '')
            elif line.startswith('mtu'):
                config['mtu'] = int(line.split(None, 1)[1])
            elif line.startswith('speed'):
                state = line.split()[1:]
                if state[0] == 'forced':
                    state = state[1]
                else:
                    state = state[0]

                if state == 'auto':
                    # Auto speed/duplex
                    continue

                # remaining options are all e.g., 10half or 40gfull
                config['speed'] = state[:-4]
                config['duplex'] = state[-4:]

            elif 'shutdown' in line:
                config['enable'] = line.startswith('no')

        return self.generate_final_config(config)
