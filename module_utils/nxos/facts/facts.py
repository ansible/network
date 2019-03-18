from ansible.module_utils.argspec.nxos.facts.facts import FactsArgs
from ansible.module_utils.argspec.nxos.interfaces.interfaces import InterfaceArgs
from ansible.module_utils.argspec.base import ArgspecBase
from ansible.module_utils.network.nxos.nxos import get_config
from ansible.module_utils.nxos.facts.base import FactsBase
from ansible.module_utils.nxos.facts.interfaces.interfaces import NxosInterfacesFacts


class Facts(ArgspecBase, FactsBase):

    argument_spec = FactsArgs.argument_spec
    VALID_SUBSETS = [
        'ansible_net_configuration_interfaces',
    ]

    def get_facts(self, module):
        gather_subset = module.params['gather_subset']
        runable_subsets = set()
        exclude_subsets = set()

        for subset in gather_subset:
            if subset == 'all':
                runable_subsets.update(self.VALID_SUBSETS)
                continue
            if subset.startswith('!'):
                subset = subset[1:]
                if subset == 'all':
                    exclude_subsets.update(self.VALID_SUBSETS)
                    continue
                exclude = True
            else:
                exclude = False

            if subset not in self.VALID_SUBSETS:
                module.fail_json(msg='Bad subset')

            if exclude:
                exclude_subsets.add(subset)
            else:
                runable_subsets.add(subset)

        if not runable_subsets:
            runable_subsets.update(self.VALID_SUBSETS)

        runable_subsets.difference_update(exclude_subsets)
        self.ansible_facts['gather_subset'] = list(runable_subsets)

        for attr in runable_subsets:
            getattr(self, '_get_%s' % attr, {})(module)

        return self.ansible_facts

    def _get_ansible_net_configuration_interfaces(self, module):
        data = get_config(module, ['| section ^interface'])
        return NxosInterfacesFacts(InterfaceArgs.argument_spec, data, 'config', 'options').populate_facts()
