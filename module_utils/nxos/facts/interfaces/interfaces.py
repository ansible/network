import re

from ansible.module_utils.network.nxos.nxos import get_interface_type
from ansible.module_utils.nxos.facts.base import FactsBase


class NxosInterfacesFacts(FactsBase):

    def populate_facts(self):
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
            facts = {'config': objs}
        return facts


    def render_config(self, generated_spec, conf):
        match = re.search(r'^(\S+)\n', conf)
        intf = match.group(1)
        if get_interface_type(intf) != 'unknown':
            name = intf
        else:
            return {}
        config = self._config_map_conf_to_obj(conf, name, spec=generated_spec)
        return config

    def _config_map_conf_to_obj(conf, name, spec):
        spec['name'] = name
        sp
        

    


    def parse_conf_arg(self, cfg, arg):
        match = re.search(r'%s (.+)(\n|$)' % arg, cfg, re.M)
        if match:
            return match.group(1).strip()
        return None

    def parse_conf_cmd_arg(self, cfg, cmd, res1, res2=None, default=None):
        match = re.search(r'\n\s+%s(\n|$)' % cmd, cfg)
        if match:
            return res1
        else:
            if res2 is not None:
                match = re.search(r'\n\s+no %s(\n|$)' % cmd, cfg)
                if match:
                    return res2
        if default is not None:
            return default
        return None
