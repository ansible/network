#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The module file for eos_facts
"""

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils. \
     eos.facts.facts import Facts

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network',}


DOCUMENTATION = """
---
module: eos_facts
version_added: 2.9
short_description: Get facts about eos devices.
description:
  - Collects facts from network devices running the eos operating
    system. This module places the facts gathered in the fact tree keyed by the
    respective resource name.  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
author: Nathaniel Case (@qalthos)
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, and net_configuration_<resource_name>.  Can specify a
        list of values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: 'all'
    version_added: "2.2"
"""

EXAMPLES = """
# Gather all facts
- eos_facts:
    gather_subset: all

# Collect only the l2_interfaces and default facts
- eos_facts:
    gather_subset:
      - net_configuration_l2_interfaces

# Do not collect l2_interfaces facts
- eos_facts:
    gather_subset:
      - "!net_configuration_l2_interfaces"
"""

RETURN = """
See the respective resource module parameters for the tree.
"""

def main():
    """
    Main entry point for module execution

    :returns: ansible_facts
    """
    module = AnsibleModule(argument_spec=Facts.argument_spec,
                           supports_check_mode=True)
    warnings = list()

    connection = Connection(module._socket_path) #pylint: disable=W0212
    gather_subset = module.params['gather_subset']
    ansible_facts = Facts().get_facts(module, connection, gather_subset)
    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)

if __name__ == '__main__':
    main()
