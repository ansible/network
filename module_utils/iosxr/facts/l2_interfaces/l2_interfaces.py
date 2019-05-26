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


class InterfacesFacts(FactsBase):
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

        if not data:
            data = connection.get('show running-config interface')

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
        intf = match.group(1)

        if get_interface_type(intf) == 'unknown':
            return {}
        # populate the facts from the configuration
        config['name'] = normalize_interface(intf)

        has_access = re.search(r"switchport access vlan (\d+)", conf)
        if has_access:
            config["access"] = {"vlan": int(has_access.group(1))}

        has_trunk = re.findall(r"switchport trunk (.+)", conf)
        if has_trunk:
            trunk = {}
            for match in has_trunk:
                has_encapsulation = re.match(r"encapsulation (\S+)", match)
                if has_encapsulation:
                    trunk["encapsulation"] = has_encapsulation.group(1)
                    continue
                has_native = re.match(r"native vlan (\d+)", match)
                if has_native:
                    trunk["native_vlan"] = int(has_native.group(1))
                    continue
                has_allowed = re.match(r"allowed vlan (\S+)", match)
                if has_allowed:
                    trunk["allowed_vlans"] = has_allowed.group(1)
                    continue
                has_pruning = re.match(r"pruning vlan (\S+)", match)
                if has_pruning:
                    trunk["pruning_vlans"] = has_pruning.group(1)
                    continue
            config['trunk'] = trunk

        return self.generate_final_config(config)