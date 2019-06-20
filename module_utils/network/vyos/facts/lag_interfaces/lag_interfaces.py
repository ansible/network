#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos lag_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from ansible.module_utils.network.vyos.vyos import load_config, run_commands
from re import findall, search, match, M
from ansible.module_utils.network. \
    vyos.facts.base import FactsBase


class Lag_interfacesFacts(FactsBase):
    """ The vyos lag_interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for lag_interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if module:  # just for linting purposes, remove
            pass
        if connection:  # just for linting purposes, remove
            pass

        if not data:
            data = connection.get_config()

        objs = []
        lag_names = findall(r'^set interfaces bonding (\S+)', data, M)
        if lag_names:
            for lag in set(lag_names):
                lag_regex = r' %s .+$' % lag
                cfg = findall(lag_regex, data, M)
                obj = self.render_config(cfg)

                output = run_commands(module, ['show interfaces bonding ' + lag + ' slaves'])
                lines = output[0].splitlines()
                members = []
                if len(lines) > 1:
                    for line in lines[2:]:
                        splitted_line = line.split()

                        if len(splitted_line) > 1:
                            members.append(splitted_line[0])
                        else:
                            members = []
                obj['name'] = lag
                obj['members'] = members

                if obj:
                    objs.append(obj)

        facts = {}
        if objs:
            facts['lag_interfaces'] = objs
        self.ansible_facts['ansible_network_resources'].update(facts)
        return self.ansible_facts

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        arp_monitor_conf = '\n'.join(filter(lambda x: ('arp-monitor' in x), conf))
        lag_conf = '\n'.join(filter(lambda x: ('bond' in x), conf))
        config = self.parse_attribs(
            ['hash-policy', 'members', 'mode', 'name', 'primary'],lag_conf
        )
        config['arp-monitor'] =  self.parse_arp_monitor(arp_monitor_conf)

        return self.generate_final_config(config)


    def parse_attribs(self, attribs, conf):
        config = {}
        for item in attribs:
            value = self.parse_conf_arg(conf, item)
            config[item] = value

        if 'disable' in conf:
            config['enable'] = False
        else:
            config['enable'] = True
        return self.generate_final_config(config)

    def parse_arp_monitor(self, conf):
        arp_monitor = None
        if conf:
            arp_monitor = {}
            target_list = []
            interval = search(r'^.*arp-monitor interval (.+)', conf, M)
            targets = findall(r"^.*arp-monitor target '(.+)'", conf, M)
            if targets:
                for target in targets:
                    target_list.append(target)
                arp_monitor['target'] = target_list
            if interval:
                value = interval.group(1).strip("'")
                arp_monitor['interval'] = int(value)
        return arp_monitor



