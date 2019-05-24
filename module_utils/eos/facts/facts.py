#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for eos
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

from ansible.module_utils.six import string_types, iteritems
from ansible.module_utils.eos.argspec.facts.facts import FactsArgs
from ansible.module_utils.eos.argspec.l2_interfaces.l2_interfaces import L2_interfacesArgs
from ansible.module_utils.eos.facts.base import FactsBase
from ansible.module_utils.eos.facts.l2_interfaces.l2_interfaces import L2_interfacesFacts


class LegacyFacts(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, list(self.COMMANDS), check_rc=False)


class Default(LegacyFacts):

    SYSTEM_MAP = {
        'serialNumber': 'serialnum',
    }

    COMMANDS = [
        'show version | json',
        'show hostname | json',
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        for key, value in iteritems(self.SYSTEM_MAP):
            if key in data:
                self.facts[value] = data[key]

        self.facts.update(self.responses[1])
        self.facts.update(self.platform_facts())

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


class Hardware(LegacyFacts):

    COMMANDS = [
        'dir all-filesystems',
        'show version | json'
    ]

    def populate(self):
        super(Hardware, self).populate()
        self.facts.update(self.populate_filesystems())
        self.facts.update(self.populate_memory())

    def populate_filesystems(self):
        data = self.responses[0]

        if isinstance(data, dict):
            data = data['messages'][0]

        fs = re.findall(r'^Directory of (.+)/', data, re.M)
        return dict(filesystems=fs)

    def populate_memory(self):
        values = self.responses[1]
        return dict(
            memfree_mb=int(values['memFree']) / 1024,
            memtotal_mb=int(values['memTotal']) / 1024
        )


class Config(LegacyFacts):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        self.facts['config'] = self.responses[0]


class Interfaces(LegacyFacts):

    INTERFACE_MAP = {
        'description': 'description',
        'physicalAddress': 'macaddress',
        'mtu': 'mtu',
        'bandwidth': 'bandwidth',
        'duplex': 'duplex',
        'lineProtocolStatus': 'lineprotocol',
        'interfaceStatus': 'operstatus',
        'forwardingModel': 'type'
    }

    COMMANDS = [
        'show interfaces | json',
        'show lldp neighbors | json'
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        data = self.responses[0]
        self.facts['interfaces'] = self.populate_interfaces(data)

        data = self.responses[1]
        if data:
            self.facts['neighbors'] = self.populate_neighbors(data['lldpNeighbors'])

    def populate_interfaces(self, data):
        facts = dict()
        for key, value in iteritems(data['interfaces']):
            intf = dict()

            for remote, local in iteritems(self.INTERFACE_MAP):
                if remote in value:
                    intf[local] = value[remote]

            if 'interfaceAddress' in value:
                intf['ipv4'] = dict()
                for entry in value['interfaceAddress']:
                    intf['ipv4']['address'] = entry['primaryIp']['address']
                    intf['ipv4']['masklen'] = entry['primaryIp']['maskLen']
                    self.add_ip_address(entry['primaryIp']['address'], 'ipv4')

            if 'interfaceAddressIp6' in value:
                intf['ipv6'] = dict()
                for entry in value['interfaceAddressIp6']['globalUnicastIp6s']:
                    intf['ipv6']['address'] = entry['address']
                    intf['ipv6']['subnet'] = entry['subnet']
                    self.add_ip_address(entry['address'], 'ipv6')

            facts[key] = intf

        return facts

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def populate_neighbors(self, neighbors):
        facts = dict()
        for value in neighbors:
            port = value['port']
            if port not in facts:
                facts[port] = list()
            lldp = dict()
            lldp['host'] = value['neighborDevice']
            lldp['port'] = value['neighborPort']
            facts[port].append(lldp)
        return facts


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config
)

class Facts(FactsArgs, FactsBase): #pylint: disable=R0903
    """ The fact class for eos
    """

    VALID_GATHER_SUBSETS = frozenset(FACT_SUBSETS.keys())

    def generate_runable_subsets(self, module, subsets, valid_subsets):
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
                    exclude_subsets.update(valid_subsets - minimal_gather_subset)
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

    def get_facts(self, module, connection, gather_subset=['!config'], gather_network_resources=['all']):
        """ Collect the facts for eos

        :param module: The module instance
        :param connection: The device connection
        :param gather_subset: The facts subset to collect
	:param gather_network_resources: The resource subset to collect
        :rtype: dict
        :returns: the facts gathered
        """
        warnings = []
        self.ansible_facts['gather_network_resources'] = list()
        self.ansible_facts['gather_subset'] = list()

        valid_network_resources_subsets = self.argument_spec['gather_network_resources'].get('choices', [])
        if valid_network_resources_subsets and 'all' in valid_network_resources_subsets:
            valid_network_resources_subsets.remove('all')

        if valid_network_resources_subsets:
            resources_runable_subsets = self.generate_runable_subsets(module, gather_network_resources, valid_network_resources_subsets)
            if resources_runable_subsets:
                self.ansible_facts['gather_network_resources'] = list(resources_runable_subsets)
                for attr in resources_runable_subsets:
                    getattr(self, '_get_%s' % attr, {})(module, connection)

        if self.VALID_GATHER_SUBSETS:
            runable_subsets = self.generate_runable_subsets(module, gather_subset, self.VALID_GATHER_SUBSETS)

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
    def _get_l2_interfaces(module, connection):
        return L2_interfacesFacts(L2_interfacesArgs. \
               argument_spec, 'config', 'options').populate_facts(module, connection)
