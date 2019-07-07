#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios vlans fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.ios.argspec.vlans.vlans import VlansArgs
import q

class VlansFacts(object):
    """ The ios vlans fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = VlansArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for vlans
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if connection:
            pass

        objs = []
        if not data:
            data = connection.get('show vlan')
        # operate on a collection of resource x

        config = data.split('\n')
        q(config)
        #
        vlan_info = ''
        for conf in config:
            if 'Name' in conf:
                vlan_info = 'Name'
            elif 'Type' in conf:
                vlan_info = 'Type'
            elif 'Remote' in conf:
                vlan_info = 'Remote'
            if conf and not ' ' in filter(None,conf.split('-')):
                obj = self.render_config(self.generated_spec, conf, vlan_info)
                if obj:
                    objs.append(obj)

        facts = {}

        if objs:
            facts['vlans'] = []
            # params = utils.validate_config(self.argument_spec, {'config': objs})

            params = {'config': objs}

            for cfg in params['config']:
                facts['vlans'].append(cfg)
        ansible_facts['ansible_network_resources'].update(facts)

        return ansible_facts

    def render_config(self, spec, conf, vlan_info):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)

        if vlan_info == 'Name' and 'Name' not in conf:
            conf = filter(None, conf.split(' '))
            q("Name: ", conf)
            config['vlan_id'] = conf[0]
            config['name'] = conf[1]
            if len(conf[2].split('/')) > 1:
                config['state'] = conf[2].split('/')[0]
                config['shutdown'] = True
            else:
                config['state'] = conf[2]
        elif vlan_info == 'Type' and 'Type' not in conf:
            conf = filter(None, conf.split(' '))
            q("Type: ", conf)
            config['mtu'] = conf[3]
                # config['name'] = normalize_interface(intf)
        # port_priority = utils.parse_conf_arg(conf, 'lacp port-priority')
        # config['port_priority'] = port_priority

        return utils.remove_empties(config)
