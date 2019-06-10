#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The module file for vyos_l3_interfaces
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type  # pylint: disable=C0103

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'network'
}

DOCUMENTATION = """
---
module: vyos_l3_interfaces
version_added: 2.9
short_description: Manages L3 interface attributes of VyOS network devices.
description: This module manages the L3 interface attributes on VyOS network devices.
author: Nilashish Chakraborty (@nilashishc)
options:
  config:
    description: The provided L3 interfaces configuration.
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Full name of the interface, e.g. eth0, eth1.
        type: str
        required: True
      ipv4:
        description:
          - List of IPv4 addresses of the interface.
        type: list
        elements: dict
        suboptions:
          address:
            description:
              - IPv4 address of the interface.
            type: str
      ipv6:
        description:
          - List of IPv6 addresses of the interface.
        type: list
        elements: dict
        suboptions:
          address:
            description:
              - IPv6 address of the interface.
            type: str
      vifs:
        description:
          - Virtual sub-interfaces L3 configurations.
        elements: dict
        type: list
        suboptions:
          vlan_id:
            description:
              - Identifier for the virtual sub-interface.
            type: str
          ipv4:
            description:
              - List of IPv4 addresses of the virtual interface.
            type: list
            elements: dict
            suboptions:
              address:
                description:
                  - IPv4 address of the virtual interface.
                type: str
          ipv6:
            description:
              - List of IPv6 addresses of the virual interface.
            type: list
            elements: dict
            suboptions:
              address:
                description:
                  - IPv6 address of the virtual interface.
                type: str
  state:
    description:
      - The state the configuration should be left in.
    type: str
    choices:
    - merged
    - replaced
    - overridden
    - deleted
    default: merged

"""
EXAMPLES = """
# Using merged
#
# Before state:
# -------------
#
# vyos:~$ show configuration commands | grep -e eth[2,3]
# set interfaces ethernet eth2 hw-id '08:00:27:c2:98:23'
# set interfaces ethernet eth3 hw-id '08:00:27:43:70:8c'
# set interfaces ethernet eth3 vif 101
# set interfaces ethernet eth3 vif 102

- name: Merge provided configuration with device configuration
  vyos_l3_interfaces:
    config:
      - name: eth2
        ipv4:
          - address: 192.0.2.10/28
          - address: 198.51.100.40/27
        ipv6:
          - address: 2001:db8:100::2/32
          - address: 2001:db8:400::10/32

      - name: eth3
        ipv4:
          - address: 203.0.113.65/26
        vifs:
          - vlan_id: 101
            ipv4:
              - address: 192.0.2.71/28
              - address: 198.51.100.131/25
          - vlan_id: 102
            ipv6:
              - address: 2001:db8:1000::5/38
              - address: 2001:db8:1400::3/38
    state: merged

# After state:
# -------------
#
# vyos:~$ show configuration commands | grep -e eth[2,3]
# set interfaces ethernet eth2 address '192.0.2.10/28'
# set interfaces ethernet eth2 address '198.51.100.40/27'
# set interfaces ethernet eth2 address '2001:db8:100::2/32'
# set interfaces ethernet eth2 address '2001:db8:400::10/32'
# set interfaces ethernet eth2 hw-id '08:00:27:c2:98:23'
# set interfaces ethernet eth3 address '203.0.113.65/26'
# set interfaces ethernet eth3 hw-id '08:00:27:43:70:8c'
# set interfaces ethernet eth3 vif 101 address '192.0.2.71/28'
# set interfaces ethernet eth3 vif 101 address '198.51.100.131/25'
# set interfaces ethernet eth3 vif 102 address '2001:db8:1000::5/38'
# set interfaces ethernet eth3 vif 102 address '2001:db8:1400::3/38'
# set interfaces ethernet eth3 vif 102 address '2001:db8:4000::2/34'


# Using replaced
#
# Before state:
# -------------
#
# vyos:~$ show configuration commands | grep eth
# set interfaces ethernet eth0 address 'dhcp'
# set interfaces ethernet eth0 duplex 'auto'
# set interfaces ethernet eth0 hw-id '08:00:27:30:f0:22'
# set interfaces ethernet eth0 smp-affinity 'auto'
# set interfaces ethernet eth0 speed 'auto'
# set interfaces ethernet eth1 hw-id '08:00:27:EA:0F:B9'
# set interfaces ethernet eth1 address '192.0.2.14/24'
# set interfaces ethernet eth2 address '192.0.2.10/24'
# set interfaces ethernet eth2 address '192.0.2.11/24'
# set interfaces ethernet eth2 address '2001:db8::10/32'
# set interfaces ethernet eth2 address '2001:db8::11/32'
# set interfaces ethernet eth2 hw-id '08:00:27:c2:98:23'
# set interfaces ethernet eth3 address '198.51.100.10/24'
# set interfaces ethernet eth3 hw-id '08:00:27:43:70:8c'
# set interfaces ethernet eth3 vif 101 address '198.51.100.130/25'
# set interfaces ethernet eth3 vif 101 address '198.51.100.131/25'
# set interfaces ethernet eth3 vif 102 address '2001:db8:4000::3/34'
# set interfaces ethernet eth3 vif 102 address '2001:db8:4000::2/34'
#
- name: Replace device configurations of listed interfaces with provided configurations
  vyos_l3_interfaces:
    config:
      - name: eth2
        ipv4:
          - address: 192.0.2.10/24

      - name: eth3
        ipv6:
          - address: 2001:db8::11/32
    state: replaced

# After state:
# -------------
#
# vyos:~$ show configuration commands | grep eth
# set interfaces ethernet eth0 address 'dhcp'
# set interfaces ethernet eth0 duplex 'auto'
# set interfaces ethernet eth0 hw-id '08:00:27:30:f0:22'
# set interfaces ethernet eth0 smp-affinity 'auto'
# set interfaces ethernet eth0 speed 'auto'
# set interfaces ethernet eth1 hw-id '08:00:27:EA:0F:B9'
# set interfaces ethernet eth1 address '192.0.2.14/24'
# set interfaces ethernet eth2 address '192.0.2.10/24'
# set interfaces ethernet eth2 hw-id '08:00:27:c2:98:23'
# set interfaces ethernet eth3 hw-id '08:00:27:43:70:8c'
# set interfaces ethernet eth3 address '2001:db8::11/32'
# set interfaces ethernet eth3 vif 101
# set interfaces ethernet eth3 vif 102


# Using overridden
#
# Before state
# --------------
#
# vyos@vyos-appliance:~$ show configuration commands | grep eth
# set interfaces ethernet eth0 address 'dhcp'
# set interfaces ethernet eth0 duplex 'auto'
# set interfaces ethernet eth0 hw-id '08:00:27:30:f0:22'
# set interfaces ethernet eth0 smp-affinity 'auto'
# set interfaces ethernet eth0 speed 'auto'
# set interfaces ethernet eth1 hw-id '08:00:27:EA:0F:B9'
# set interfaces ethernet eth1 address '192.0.2.14/24'
# set interfaces ethernet eth2 address '192.0.2.10/24'
# set interfaces ethernet eth2 address '192.0.2.11/24'
# set interfaces ethernet eth2 address '2001:db8::10/32'
# set interfaces ethernet eth2 address '2001:db8::11/32'
# set interfaces ethernet eth2 hw-id '08:00:27:c2:98:23'
# set interfaces ethernet eth3 address '198.51.100.10/24'
# set interfaces ethernet eth3 hw-id '08:00:27:43:70:8c'
# set interfaces ethernet eth3 vif 101 address '198.51.100.130/25'
# set interfaces ethernet eth3 vif 101 address '198.51.100.131/25'
# set interfaces ethernet eth3 vif 102 address '2001:db8:4000::3/34'
# set interfaces ethernet eth3 vif 102 address '2001:db8:4000::2/34'

- name: Overrides all device configuration with provided configuration
  vyos_l3_interfaces:
    config:
      - name: eth0
        ipv4:
          - address: dhcp
        ipv6:
          - address: dhcpv6
    state: overridden

# After state
# ------------
#
# vyos@vyos-appliance:~$ show configuration commands | grep eth
# set interfaces ethernet eth0 address 'dhcp'
# set interfaces ethernet eth0 address 'dhcpv6'
# set interfaces ethernet eth0 duplex 'auto'
# set interfaces ethernet eth0 hw-id '08:00:27:30:f0:22'
# set interfaces ethernet eth0 smp-affinity 'auto'
# set interfaces ethernet eth0 speed 'auto'
# set interfaces ethernet eth1 hw-id '08:00:27:EA:0F:B9'
# set interfaces ethernet eth2 hw-id '08:00:27:c2:98:23'
# set interfaces ethernet eth3 hw-id '08:00:27:43:70:8c'
# set interfaces ethernet eth3 vif 101
# set interfaces ethernet eth3 vif 102


# Using deleted
#
# Before state
# -------------
# vyos@vyos-appliance:~$ show configuration commands | grep eth
# set interfaces ethernet eth0 address 'dhcp'
# set interfaces ethernet eth0 duplex 'auto'
# set interfaces ethernet eth0 hw-id '08:00:27:30:f0:22'
# set interfaces ethernet eth0 smp-affinity 'auto'
# set interfaces ethernet eth0 speed 'auto'
# set interfaces ethernet eth1 hw-id '08:00:27:EA:0F:B9'
# set interfaces ethernet eth1 address '192.0.2.14/24'
# set interfaces ethernet eth2 address '192.0.2.10/24'
# set interfaces ethernet eth2 address '192.0.2.11/24'
# set interfaces ethernet eth2 address '2001:db8::10/32'
# set interfaces ethernet eth2 address '2001:db8::11/32'
# set interfaces ethernet eth2 hw-id '08:00:27:c2:98:23'
# set interfaces ethernet eth3 address '198.51.100.10/24'
# set interfaces ethernet eth3 hw-id '08:00:27:43:70:8c'
# set interfaces ethernet eth3 vif 101 address '198.51.100.130/25'
# set interfaces ethernet eth3 vif 101 address '198.51.100.131/25'
# set interfaces ethernet eth3 vif 102 address '2001:db8:4000::3/34'
# set interfaces ethernet eth3 vif 102 address '2001:db8:4000::2/34'

- name: Delete L3 attributes of given interfaces (Note: This won't delete the interface itself)
  vyos_l3_interfaces:
    config:
      - name: eth1
      - name: eth2
      - name: eth3
    state: deleted

# After state
# ------------
# vyos@vyos-appliance:~$ show configuration commands | grep eth
# set interfaces ethernet eth0 address 'dhcp'
# set interfaces ethernet eth0 duplex 'auto'
# set interfaces ethernet eth0 hw-id '08:00:27:f3:6c:b5'
# set interfaces ethernet eth0 smp_affinity 'auto'
# set interfaces ethernet eth0 speed 'auto'
# set interfaces ethernet eth1 hw-id '08:00:27:ad:ef:65'
# set interfaces ethernet eth1 smp_affinity 'auto'
# set interfaces ethernet eth2 hw-id '08:00:27:ab:4e:79'
# set interfaces ethernet eth2 smp_affinity 'auto'
# set interfaces ethernet eth3 hw-id '08:00:27:17:3c:85'
# set interfaces ethernet eth3 smp_affinity 'auto'


"""
RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  sample: >
    The configuration returned will always be in the same format
    of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
  sample: >
    The configuration returned will always be in the same format
    of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample:
    - 'set interfaces ethernet eth1 address '192.0.2.14/24''
    - 'set interfaces ethernet eth3 vif 101 address '192.0.2.71/28''
"""


# pylint: disable=C0413
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network. \
    vyos.config.l3_interfaces.l3_interfaces import L3_interfaces
# pylint: enable=C0413


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=L3_interfaces.argument_spec,
                           supports_check_mode=True)

    result = L3_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
