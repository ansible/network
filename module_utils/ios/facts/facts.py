#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for ios
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

from ansible.module_utils.ios.argspec.facts.facts import FactsArgs
from ansible.module_utils.ios.facts.base import FactsBase
from ansible.module_utils.ios.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils.ios.facts.interfaces.interfaces import InterfacesFacts


class Facts(FactsArgs, FactsBase):
    """ The fact class for ios
    """

    def get_facts(self, module, connection, gather_subset=['all']):
        """ Collect the facts for ios

        :param module: The module instance
        :param connection: The device connection
        :param gather_subset: The facts subset to collect
        :rtype: dict
        :returns: the facts gathered
        """
        valid_subsets = self.argument_spec['gather_subset'].get('choices', [])
        if valid_subsets and 'all' in valid_subsets:
            valid_subsets.remove('all')

        runable_subsets = set()
        exclude_subsets = set()

        for subset in gather_subset:
            if subset == 'all':
                runable_subsets.update(valid_subsets)
                continue
            if subset.startswith('!'):
                subset = subset[1:]
                if subset == 'all':
                    exclude_subsets.update(valid_subsets)
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
        self.ansible_facts['gather_subset'] = list(runable_subsets)

        for attr in runable_subsets:
            getattr(self, '_get_%s' % attr, {})(module, connection)

        return self.ansible_facts

    @staticmethod
    def _get_net_configuration_interfaces(module, connection):
        return InterfacesFacts(InterfacesArgs.argument_spec, 'config', 'options').populate_facts(module, connection)

