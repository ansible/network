from ansible.module_utils.argspec.base import ArgspecBase


class ConfigBase(ArgspecBase):

    def search_obj_in_list(self, name, lst):
        for o in lst:
            if o['name'] == name:
                return o
        return None

    def normalize_interface(self, name):
        """Return the normalized interface name
        """
        if not name:
            return

        def _get_number(name):
            digits = ''
            for char in name:
                if char.isdigit() or char in '/.':
                    digits += char
            return digits

        if name.lower().startswith('et'):
            if_type = 'Ethernet'
        elif name.lower().startswith('vl'):
            if_type = 'Vlan'
        elif name.lower().startswith('lo'):
            if_type = 'loopback'
        elif name.lower().startswith('po'):
            if_type = 'port-channel'
        elif name.lower().startswith('nv'):
            if_type = 'nve'
        else:
            if_type = None

        number_list = name.split(' ')
        if len(number_list) == 2:
            number = number_list[-1].strip()
        else:
            number = _get_number(name)

        if if_type:
            proper_interface = if_type + number
        else:
            proper_interface = name

        return proper_interface

    def get_interface_type(self, interface):
        """Gets the type of interface
        """
        if interface.upper().startswith('ET'):
            return 'ethernet'
        elif interface.upper().startswith('VL'):
            return 'svi'
        elif interface.upper().startswith('LO'):
            return 'loopback'
        elif interface.upper().startswith('MG'):
            return 'management'
        elif interface.upper().startswith('MA'):
            return 'management'
        elif interface.upper().startswith('PO'):
            return 'portchannel'
        elif interface.upper().startswith('NV'):
            return 'nve'
        else:
            return 'unknown'
