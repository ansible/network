from copy import deepcopy

from ansible.module_utils.network.nxos.nxos import get_interface_type, normalize_interface
from ansible.module_utils.nxos.facts.base import FactsBase


class NxosInterfacesFacts(FactsBase):

    def populate_facts(self):
        """
        Populate nxos interfaces facts
        """
        objs = []
        if self.data is None:
            return {}

        config = self.data.split('interface ')
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)

        facts = {}
        if objs:
            facts['interfaces'] = obj
        self.ansible_facts['ansible_net_configuration'].update(facts)
        return self.ansible_facts

    def render_config(self, spec, conf):
        """
        Render config in dictionary structure and delete keys from spec for null values
        """
        config = deepcopy(spec)

        match = re.search(r'^(\S+)\n', conf)
        intf = match.group(1)
        name = get_interface_type(intf)
        if name == 'unknown':
            return {}
        config['name'] = normalize_interface(name)

        config['description'] = if self.parse_conf_arg(conf, 'description') else del config['description']
        config['speed'] = if self.parse_conf_arg(conf, 'speed') else del config['speed']
        config['mtu'] = if self.parse_conf_arg(conf, 'mtu') else del config['mtu']
        config['duplex'] = if self.parse_conf_arg(conf, 'duplex') else del config['duplex']
        cofig['mode'] = if self.parse_conf_cmd_arg(conf, 'switchport', 'layer2', res2='layer3') else del config['mode']
        config['enable'] = if self.parse_conf_cmd_arg(conf, 'shutdown', False)
        config['fabric_forwarding_anycast_gateway'] = if self.parse_conf_cmd_arg(conf, 'fabric forwarding mode anycast-gateway', True, res2=False) else del config['fabric_forwarding_anycast_gateway']
        config['ip_forward'] = if self.parse_conf_cmd_arg(conf, 'ip forward', 'enable', res2='disable') else del config['ip_forward']

        return config
