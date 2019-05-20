#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: nxos_facts
extends_documentation_fragment: nxos
version_added: "2.9"
short_description: Gets facts about NX-OS switches
description:
  - Collects facts from Cisco Nexus devices running the NX-OS operating
    system.  Fact collection is supported over both Cli and Nxapi
    transports.  This module prepends all of the base network fact keys
    with C(ansible_net_<fact>).  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
author:
  - Trishna Guha (@trishnaguha)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all, min, hardware, config, legacy, and interfaces. Can specify a
        list of values to include a larger subset.Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: '!config'
    version_added: "2.2"
  gather_network_resources:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all and the resources like interfaces, vlans etc.
        Can specify a list of values to include a larger subset. Values
        can also be used with an initial C(M(!)) to specify that a
        specific subset should not be collected.
    required: false
    version_added: "2.9"
"""

EXAMPLES = """
# Gather all facts
- nxos_facts:
    gather_subset: all
    gather_network_resources: all

# Collect only the interfaces facts
- nxos_facts:
    gather_subset:
      - !all
      - !min
    gather_network_resources:
      - interfaces

# Do not collect interfaces facts
- nxos_facts:
    gather_network_resources:
      - "!interfaces"

# Collect interfaces and default facts
- nxos_facts:
    gather_subset: min
    gather_network_resources: interfaces
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list
ansible_gather_network_resources:
  description: The list of fact resource subsets collected from the device
  returned: always
  type: list
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec
from ansible.module_utils.nxos.facts.facts import Facts


def main():
    argument_spec = Facts.argument_spec
    argument_spec.update(nxos_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)
    warnings = ['default value for `gather_subset` will be changed to `min` from `!config` v2.11 onwards']

    connection = Connection(module._socket_path)
    gather_subset = module.params['gather_subset']
    gather_network_resources = module.params['gather_network_resources']
    result = Facts().get_facts(module, connection, gather_subset, gather_network_resources)

    ansible_facts, additional_warnings = result
    warnings.extend(additional_warnings)

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
