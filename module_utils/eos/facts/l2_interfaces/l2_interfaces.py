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
import re

from ansible.module_utils.eos.facts.base import FactsBase


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
        if not data:
            data = connection.get('show running-config | section ^interface')

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
        config = deepcopy(spec)

        # populate the facts from the configuration
        config['name'] = re.match(r'(\S+)', conf).group(1).replace('"', '')

        has_access = re.search(r"switchport access vlan (\d+)", conf)
        if has_access:
            config["access"] = {"vlan": int(has_access.group(1))}

        has_trunk = re.findall(r"switchport trunk (.+)", conf)
        if has_trunk:
            trunk = {}
            for match in has_trunk:
                has_native = re.match(r"native vlan (\d+)", match)
                if has_native:
                    trunk["native_vlan"] = int(has_native.group(1))
                    continue

                has_allowed = re.match(r"allowed vlan (\S+)", match)
                if has_allowed:
                    # TODO: listify?
                    trunk["trunk_allowed_vlans"] = has_allowed.group(1)
                    continue
            config['trunk'] = trunk

        return self.generate_final_config(config)
