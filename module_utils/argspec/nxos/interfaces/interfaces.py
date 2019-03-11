from ansible.module_utils.argspec.base import ArgspecBase

class InterfaceArgs(ArgspecBase):

    config_spec = {
        'name': dict(type='str', required=True),
        'description': dict(),
        'enable': dict(default=True, type=bool),
        'speed': dict(),
        'mode': dict(choices=['layer2', 'layer3']),
        'mtu': dict(),
        'duplex': dict(choices=['full', 'half', 'auto']),
        'mode': dict(choices=['layer2', 'layer3']),
        'ip_forward': dict(choices=['enable', 'disable']),
        'fabric_forwarding_anycast_gateway': dict(type='bool'),
    }

    argument_spec = {
        'operation': dict(default='merge', choices=['merge', 'replace', 'override', 'delete']),
        'config': dict(type='list', elements='dict', options=config_spec)
    }
