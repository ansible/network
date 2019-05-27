#!/usr/bin/python
# -*- coding: utf-8 -*-
# {{ rm['COPYRIGHT'] }}
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The module file for iosxr_facts
"""

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

NETWORK_OS = "iosxr"
RESOURCE = "facts"
COPYRIGHT = "Copyright 2019 Red Hat"

DOCUMENTATION = """
---
module: iosxr_facts
version_added: 2.9
short_description: Get facts about Cisco IOSXR devices.
description:
  - Collects facts from network devices running the iosxr operating
    system. This module places the facts gathered in the fact tree keyed by the
    respective resource name.  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
author: [u'Sumit Jaiswal (@justjais)']
notes:
  - Tested against IOSXRv Version 6.1.3 on VIRL
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all, min, hardware, config, legacy, and interfaces. Can specify a
        list of values to include a larger subset. Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: 'all'
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
- iosxr_facts:
    gather_subset: all
    gather_network_resources: all

# Collect only the iosxr facts
- iosxr_facts:
    gather_subset:
      - !all
      - !min
    gather_network_resources:
      - iosxr

# Do not collect iosxr facts
- iosxr_facts:
    gather_network_resources:
      - "!iosxr"

# Collect iosxr and minimal default facts
- iosxr_facts:
    gather_subset: min
    gather_network_resources: iosxr
"""

RETURN = """
See the respective resource module parameters for the tree.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.iosxr.facts.facts import Facts

def main():
    """
    Main entry point for module execution

    :returns: ansible_facts
    """
    module = AnsibleModule(argument_spec=Facts.argument_spec,
                           supports_check_mode=True)
    warnings = ['default value for `gather_subset` will be changed to `min` from `!config` v2.11 onwards']

    connection = Connection(module._socket_path)
    gather_subset = module.params['gather_subset']
    gather_network_resources = module.params['gather_network_resources']
    result = Facts().get_facts(module, connection, gather_subset, gather_network_resources)
    
    try:
        ansible_facts, warning = result
        warnings.extend(warning)
    except (TypeError, KeyError):
        ansible_facts = result

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()

