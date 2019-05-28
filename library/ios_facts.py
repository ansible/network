#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The module file for ios_facts
"""

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': [u'preview'],
                    'supported_by': [u'Ansible Network']}


DOCUMENTATION = """
---
module: ios_facts
version_added: 2.9
short_description: Collect facts from remote devices running Cisco IOS
description:
  - Collects a base set of device facts from a remote device that
    is running IOS.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
author: [u'Sumit Jaiswal (@justjais)']
notes:
  - Tested against IOS Version 15.6(3)M2 on VIRL
options:
  gather_subset:
    description:
      - When supplied, this argument restricts the facts collected
         to a given subset.
      - Possible values for this argument include
         C(all), C(hardware), C(config), and C(interfaces).
      - Specify a list of values to include a larger subset.
      - Use a value with an initial C(!) to collect all facts except that subset.
    required: false
    default: '!config'
"""

EXAMPLES = """
# Gather all facts
- ios_facts:
    gather_subset: all
    gather_network_resources: all
# Collect only the ios facts
- ios_facts:
    gather_subset:
      - !all
      - !min
    gather_network_resources:
      - ios
# Do not collect ios facts
- ios_facts:
    gather_network_resources:
      - "!ios"
# Collect ios and minimal default facts
- ios_facts:
    gather_subset: min
    gather_network_resources: ios
"""

RETURN = """
See the respective resource module parameters for the tree.
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.ios.facts.facts import Facts


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
