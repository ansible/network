from ansible.module_utils.nxos.argspec.facts.facts import FactsArgs
from ansible.module_utils.nxos.argspec.interfaces.interfaces import InterfaceArgs
from ansible.module_utils.nxos.facts.base import FactsBase
from ansible.module_utils.nxos.facts.interfaces.interfaces import InterfacesFacts


class Facts(FactsArgs, FactsBase):

    def get_facts(self, module, connection, gather_subset=['all']):
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

    def _get_net_configuration_interfaces(self, module, connection):
        return InterfacesFacts(InterfaceArgs.argument_spec, 'config', 'options').populate_facts(module, connection)
