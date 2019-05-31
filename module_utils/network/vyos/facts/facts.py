#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for vyos
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

import platform
import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.network. \
    vyos.argspec.facts.facts import FactsArgs
from ansible.module_utils.network. \
    vyos.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils.network. \
    vyos.facts.base import FactsBase
from ansible.module_utils.network. \
    vyos.facts.interfaces.interfaces import InterfacesFacts
from ansible.module_utils. \
    network.vyos.vyos import run_commands, get_capabilities


class LegacyFactsBase(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, list(self.COMMANDS))


class Default(LegacyFactsBase):

    COMMANDS = [
        'show version',
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        self.facts['serialnum'] = self.parse_serialnum(data)
        self.facts.update(self.platform_facts())

    def parse_serialnum(self, data):
        match = re.search(r'HW S/N:\s+(\S+)', data)
        if match:
            return match.group(1)

    def platform_facts(self):
        platform_facts = {}

        resp = get_capabilities(self.module)
        device_info = resp['device_info']

        platform_facts['system'] = device_info['network_os']

        for item in ('model', 'image', 'version', 'platform', 'hostname'):
            val = device_info.get('network_os_%s' % item)
            if val:
                platform_facts[item] = val

        platform_facts['api'] = resp['network_api']
        platform_facts['python_version'] = platform.python_version()

        return platform_facts


class Config(LegacyFactsBase):

    COMMANDS = [
        'show configuration commands',
        'show system commit',
    ]

    def populate(self):
        super(Config, self).populate()

        self.facts['config'] = self.responses

        commits = self.responses[1]
        entries = list()
        entry = None

        for line in commits.split('\n'):
            match = re.match(r'(\d+)\s+(.+)by(.+)via(.+)', line)
            if match:
                if entry:
                    entries.append(entry)

                entry = dict(revision=match.group(1),
                             datetime=match.group(2),
                             by=str(match.group(3)).strip(),
                             via=str(match.group(4)).strip(),
                             comment=None)
            else:
                entry['comment'] = line.strip()

        self.facts['commits'] = entries


class Neighbors(LegacyFactsBase):

    COMMANDS = [
        'show lldp neighbors',
        'show lldp neighbors detail',
    ]

    def populate(self):
        super(Neighbors, self).populate()

        all_neighbors = self.responses[0]
        if 'LLDP not configured' not in all_neighbors:
            neighbors = self.parse(
                self.responses[1]
            )
            self.facts['neighbors'] = self.parse_neighbors(neighbors)

    def parse(self, data):
        parsed = list()
        values = None
        for line in data.split('\n'):
            if not line:
                continue
            elif line[0] == ' ':
                values += '\n%s' % line
            elif line.startswith('Interface'):
                if values:
                    parsed.append(values)
                values = line
        if values:
            parsed.append(values)
        return parsed

    def parse_neighbors(self, data):
        facts = dict()
        for item in data:
            interface = self.parse_interface(item)
            host = self.parse_host(item)
            port = self.parse_port(item)
            if interface not in facts:
                facts[interface] = list()
            facts[interface].append(dict(host=host, port=port))
        return facts

    def parse_interface(self, data):
        match = re.search(r'^Interface:\s+(\S+),', data)
        return match.group(1)

    def parse_host(self, data):
        match = re.search(r'SysName:\s+(.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_port(self, data):
        match = re.search(r'PortDescr:\s+(.+)$', data, re.M)
        if match:
            return match.group(1)


FACT_SUBSETS = dict(
    default=Default,
    neighbors=Neighbors,
    config=Config
)


class Facts(FactsArgs, FactsBase):  # pylint: disable=R0903
    """ The fact class for vyos
    """

    VALID_GATHER_SUBSETS = frozenset(FACT_SUBSETS.keys())

    @staticmethod
    def gen_runable(module, subsets, valid_subsets):
        """ Generate the runable subset

        :param module: The module instance
        :param subsets: The provided subsets
        :param valid_subsets: The valid subsets
        :rtype: list
        :returns: The runable subsets
        """
        runable_subsets = set()
        exclude_subsets = set()
        minimal_gather_subset = frozenset(['default'])

        for subset in subsets:
            if subset == 'all':
                runable_subsets.update(valid_subsets)
                continue
            if subset == 'min' and minimal_gather_subset:
                runable_subsets.update(minimal_gather_subset)
                continue
            if subset.startswith('!'):
                subset = subset[1:]
                if subset == 'min':
                    exclude_subsets.update(minimal_gather_subset)
                    continue
                if subset == 'all':
                    exclude_subsets.update(
                        valid_subsets - minimal_gather_subset)
                    continue
                exclude = True
            else:
                exclude = False

            if subset not in valid_subsets:
                module.fail_json(msg='Bad subset')

            if exclude:
                exclude_subsets.add(subset)
            else:
                runable_subsets.add(subset)

        if not runable_subsets:
            runable_subsets.update(valid_subsets)
        runable_subsets.difference_update(exclude_subsets)

        return runable_subsets

    def get_facts(self, module, connection, gather_subset=None,
                  gather_network_resources=None):
        """ Collect the facts for vyos

        :param module: The module instance
        :param connection: The device connection
        :param gather_subset: The facts subset to collect
        :param gather_network_resources: The resource subset to collect
        :rtype: dict
        :returns: the facts gathered
        """
        if not gather_subset:
            gather_subset = ['!config']
        if not gather_network_resources:
            gather_network_resources = ['all']
        warnings = []
        self.ansible_facts['gather_network_resources'] = list()
        self.ansible_facts['gather_subset'] = list()

        valnetres = self.argument_spec['gather_network_resources'].\
            get('choices', [])
        if valnetres:
            if 'all' in valnetres:
                valnetres.remove('all')

        if valnetres:
            restorun = self.gen_runable(module, gather_network_resources,
                                        valnetres)
            if restorun:
                self.ansible_facts['gather_network_resources'] = list(restorun)
                for attr in restorun:
                    getattr(self, '_get_%s' % attr, {})(module, connection)

        if self.VALID_GATHER_SUBSETS:
            runable_subsets = self.gen_runable(module,
                                               gather_subset,
                                               self.VALID_GATHER_SUBSETS)

            if runable_subsets:
                facts = dict()
                self.ansible_facts['gather_subset'] = list(runable_subsets)

                instances = list()
                for key in runable_subsets:
                    instances.append(FACT_SUBSETS[key](module))

                for inst in instances:
                    inst.populate()
                    facts.update(inst.facts)
                    warnings.extend(inst.warnings)

                for key, value in iteritems(facts):
                    key = 'ansible_net_%s' % key
                    self.ansible_facts[key] = value

        return self.ansible_facts, warnings

    @staticmethod
    def _get_interfaces(module, connection):
        return InterfacesFacts(
            InterfacesArgs.argument_spec,
            'config', 'options').populate_facts(module, connection)
