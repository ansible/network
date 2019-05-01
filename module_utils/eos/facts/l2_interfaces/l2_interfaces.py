#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos l2_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from copy import deepcopy
from ansible.module_utils. \
     eos.facts.base import FactsBase

class L2_interfacesFacts(FactsBase):
    """ The eos l2_interfaces fact class
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

        if not data:
            data = "foo" # connection.get('show running-config | section ^interface')

        # operate on a collection of resource x
        config = [data] # data.split('interface ')
        objs = []
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            facts['l2_interfaces'] = objs
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
        config = {"some": "value"}
        return self.generate_final_config(config)
