from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list

from ansible.module_utils.argspec.nxos.interfaces.interfaces import InterfaceArgs
from ansible.module_utils.nxos.config.base import ConfigBase
from ansible.module_utils.nxos.facts.facts import NxosFacts
from ansible.module_utils.nxos.utils.utils import get_interface_type, normalize_interface, search_obj_in_list


class Interface(ConfigBase, InterfaceArgs):

    gather_subset = [
        'net_configuration_interfaces',
    ]

    def get_interface_facts(self):
        facts = NxosFacts().get_facts(self._module, self._connection, self.gather_subset)
        interface_facts = facts['net_configuration'].get('interfaces')
        if not interface_facts:
            return []
        return interface_facts

    def execute_module(self):
        result = {'changed': False}
        commands = list()
        warnings = list()

        commands.extend(self.set_config())
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        interface_facts = self.get_interface_facts()

        if result['changed'] == False:
            result['before'] = interface_facts
        elif result['changed'] == True:
            result['after'] = interface_facts

        result['warnings'] = warnings
        return result

    def set_config(self):
        want = self._config_map_params_to_obj()
        have = self.get_interface_facts()
        resp = self.set_state(want, have)
        return to_list(resp)

    def _config_map_params_to_obj(self):
        objs = []
        collection = self._module.params['config']
        for config in collection:
            obj = {
                'name': normalize_interface(config['name']),
                'description': config['description'],
                'enable': config['enable'],
                'speed': config['speed'],
                'mtu': config['mtu'],
                'duplex': config['duplex'],
                'mode': config['mode'],
                'ip_forward': config['ip_forward'],
                'fabric_forwarding_anycast_gateway': config['fabric_forwarding_anycast_gateway'],
            }
            objs.append(obj)

        return objs

    def set_state(self, want, have):
        commands = list()

        state = self._module.params['state']
        if state == 'overriden':
            commands.extend(self._state_overriden(want, have))
        else:
            for w in want:
                name = w['name']
                interface_type = get_interface_type(name)
                obj_in_have = search_obj_in_list(name, have)
                if state == 'deleted' and obj_in_have:
                    commands.append('no interface {0}'.format(w['name']))

                if state == 'merged':
                    commands.extend(self._state_merged(w, obj_in_have, interface_type))

                if state == 'replaced':
                    commands.extend(self._state_replaced(w, obj_in_have, interface_type))

        return commands

    def _state_replaced(self, w, obj_in_have, interface_type):
        commands = list()

        if interface_type in ('loopback', 'portchannel', 'svi'):
            commands.append('no interface {0}'. format(w['name']))
            commands.extend(self._state_merged(w, obj_in_have, interface_type))
        else:
            commands.append('default interface {0}'.format(w['name']))
            commands.extend(self._state_merged(w, obj_in_have, interface_type))

        return commands

    def _state_overriden(self, want, have):
        """
        purge interfaces
        """
        commands = list()

        for h in have:
            name = h['name']
            obj_in_want = search_obj_in_list(name, want)
            if not obj_in_want:
                interface_type = get_interface_type(name)

                # Remove logical interfaces
                if interface_type in ('loopback', 'portchannel', 'svi'):
                    commands.append('no interface {0}'.format(name))
                elif interface_type == 'ethernet':
                    default = True
                    if h['enable'] is True:
                        keys = ('description', 'mode', 'mtu', 'speed', 'duplex', 'ip_forward','fabric_forwarding_anycast_gateway')
                        for k, v in iteritems(h):
                            if k in keys:
                                if h[k] is not None:
                                    default = False
                                    break
                    else:
                        default = False

                    if default is False:
                        # Put physical interface back into default state
                        commands.append('default interface {0}'.format(name))

        for w in want:
            name = w['name']
            interface_type = get_interface_type(name)
            obj_in_have = search_obj_in_list(name, have)
            commands.extend(self._state_merged( w, obj_in_have, interface_type))

        return commands

    def _state_merged(self, w, obj_in_have, interface_type):
        commands = list()

        args = ('speed', 'description', 'duplex', 'mtu')
        name = w['name']
        mode = w['mode']
        ip_forward = w['ip_forward']
        fabric_forwarding_anycast_gateway = w['fabric_forwarding_anycast_gateway']
        enable = w['enable']

        if name:
            interface = 'interface ' + name

        if not obj_in_have:
            commands.append(interface)
            if interface_type in ('ethernet', 'portchannel'):
                if mode == 'layer2':
                    commands.append('switchport')
                elif mode == 'layer3':
                    commands.append('no switchport')

            if enable is True:
                commands.append('no shutdown')
            elif enable is False:
                commands.append('shutdown')

            if ip_forward == 'enable':
                commands.append('ip forward')
            elif ip_forward == 'disable':
                commands.append('no ip forward')

            if fabric_forwarding_anycast_gateway is True:
                commands.append('fabric forwarding mode anycast-gateway')
            elif fabric_forwarding_anycast_gateway is False:
                commands.append('no fabric forwarding mode anycast-gateway')

            for item in args:
                candidate = w.get(item)
                if candidate:
                    commands.append(item + ' ' + str(candidate))

        else:
            if interface_type in ('ethernet', 'portchannel'):
                if mode == 'layer2' and mode != obj_in_have.get('mode'):
                    self._add_command_to_interface(interface, 'switchport', commands)
                elif mode == 'layer3' and mode != obj_in_have.get('mode'):
                    self._add_command_to_interface(interface, 'no switchport', commands)

            if enable is True and enable != obj_in_have.get('enable'):
                self._add_command_to_interface(interface, 'no shutdown', commands)
            elif enable is False and enable != obj_in_have.get('enable'):
                self._add_command_to_interface(interface, 'shutdown', commands)

            if ip_forward == 'enable' and ip_forward != obj_in_have.get('ip_forward'):
                self._add_command_to_interface(interface, 'ip forward', commands)
            elif ip_forward == 'disable' and ip_forward != obj_in_have.get('ip forward'):
                self._add_command_to_interface(interface, 'no ip forward', commands)

            if (fabric_forwarding_anycast_gateway is True and obj_in_have.get('fabric_forwarding_anycast_gateway') is False):
                self._add_command_to_interface(interface, 'fabric forwarding mode anycast-gateway', commands)

            elif (fabric_forwarding_anycast_gateway is False and obj_in_have.get('fabric_forwarding_anycast_gateway') is True):
                self._add_command_to_interface(interface, 'no fabric forwarding mode anycast-gateway', commands)

            for item in args:
                candidate = w.get(item)
                if candidate and candidate != obj_in_have.get(item):
                    cmd = item + ' ' + str(candidate)
                    self._add_command_to_interface(interface, cmd, commands)

            # if the mode changes from L2 to L3, the admin state
            # seems to change after the API call, so adding a second API
            # call to ensure it's in the desired state.
            if name and interface_type == 'ethernet':
                if mode and mode != obj_in_have.get('mode'):
                    enable = w.get('enable') or obj_in_have.get('enable')
                    if enable is True:
                        commands.append(self._get_admin_state(enable))

        return commands

    def _get_admin_state(self, enable):
        command = ''
        if enable is True:
            command = 'no shutdown'
        elif enable is False:
            command = 'shutdown'
        return command

    def _add_command_to_interface(self, interface, cmd, commands):
        if interface not in commands:
            commands.append(interface)
        commands.append(cmd)
