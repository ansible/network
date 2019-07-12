#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for vyos
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

import platform
import re
from ansible.module_utils.network.vyos.argspec.facts.facts import FactsArgs
from ansible.module_utils.network.common.facts.facts import FactsBase
from ansible.module_utils.network.vyos.facts.lldp.lldp import LldpFacts
from ansible.module_utils.network.vyos.vyos import run_commands, get_capabilities


class LegacyFactsBase(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.warnings = list()
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


FACT_LEGACY_SUBSETS = dict(
    default=Default,
    neighbors=Neighbors,
    config=Config
)
FACT_RESOURCE_SUBSETS = dict(
    lldp=LldpFacts,
)


class Facts(FactsBase):
    """ The fact class for vyos
    """

    VALID_LEGACY_GATHER_SUBSETS = frozenset(FACT_LEGACY_SUBSETS.keys())
    VALID_RESOURCE_SUBSETS = frozenset(FACT_RESOURCE_SUBSETS.keys())

    def __init__(self, module):
        super(Facts, self).__init__(module)

    def get_facts(self, legacy_facts_type=None, resource_facts_type=None, data=None):
        """ Collect the facts for vyos

        :param legacy_facts_type: List of legacy facts types
        :param resource_facts_type: List of resource fact types
        :param data: previously collected conf
        :rtype: dict
        :return: the facts gathered
        """
        netres_choices = FactsArgs.argument_spec['gather_network_resources'].get('choices', [])
        if self.VALID_RESOURCE_SUBSETS:
            self.get_network_resources_facts(
                netres_choices, FACT_RESOURCE_SUBSETS, resource_facts_type, data
            )

        if self.VALID_LEGACY_GATHER_SUBSETS:
            self.get_network_legacy_facts(FACT_LEGACY_SUBSETS, legacy_facts_type)

        return self.ansible_facts, self._warnings
