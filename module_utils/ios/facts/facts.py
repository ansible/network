#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for ios
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

from ansible.module_utils.six import iteritems

from ansible.module_utils.ios.argspec.facts.facts import FactsArgs
from ansible.module_utils.ios.facts.base import FactsBase
from ansible.module_utils.ios.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils.ios.facts.interfaces.interfaces import InterfacesFacts


FACT_SUBSETS = {}

class Facts(FactsArgs, FactsBase): #pylint: disable=R0903
    """ The fact class for ios
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
        """ Collect the facts for ios
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

        if warnings:
            return self.ansible_facts, warnings
        else:
            return self.ansible_facts


    @staticmethod
    def _get_interfaces(module, connection):
        return InterfacesFacts(InterfacesArgs.argument_spec, 'config', 'options').populate_facts(module, connection)