import re

from copy import deepcopy

from ansible.module_utils.nxos.facts.base import FactsBase
from ansible.module_utils.nxos.utils.utils import get_interface_type, normalize_interface


class NxosInterfacesFacts(FactsBase):

    def populate_facts(self, module, connection, data=None):
        """
        Populate nxos interfaces facts
        """
        objs = []

        if not data:
           data = connection.get('show running-config | section ^interface')

        config = data.split('interface ')
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)

        facts = {}
        if objs:
            facts['interfaces'] = objs
        self.ansible_facts['net_configuration'].update(facts)
        return self.ansible_facts

    def render_config(self, spec, conf):
        """
        Render config in dictionary structure and delete keys from spec for null values
        """
        config = deepcopy(spec)

        match = re.search(r'^(\S+)\n', conf)
        intf = match.group(1)
        if get_interface_type(intf) == 'unknown':
            return {}
        config['name'] = normalize_interface(intf)

        config['description'] = self.parse_conf_arg(conf, 'description')
        config['speed'] = self.parse_conf_arg(conf, 'speed')
        config['mtu'] = self.parse_conf_arg(conf, 'mtu')
        config['duplex'] = self.parse_conf_arg(conf, 'duplex')
        config['mode'] = self.parse_conf_cmd_arg(conf, 'switchport', 'layer2', res2='layer3')
        enable = self.parse_conf_cmd_arg(conf, 'shutdown', False)
        config['enable'] = enable if enable is not None else config['enable']
        config['fabric_forwarding_anycast_gateway'] = self.parse_conf_cmd_arg(conf, 'fabric forwarding mode anycast-gateway', True, res2=False)
        config['ip_forward'] = self.parse_conf_cmd_arg(conf, 'ip forward', 'enable', res2='disable')

        return self.generate_final_config(config)
