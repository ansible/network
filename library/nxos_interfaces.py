#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: interfaces
version_added: "2.8"
short_description: Manages physical attributes of interfaces on Cisco NX-OS devices.
description:
  - Manages physical attributes of interfaces of NX-OS switches.
author:
  - Trishna Guha (@trishnaguha)
options: {}
"""

EXAMPLES = """
- name: Configure interfaces
  nxos_interfaces:
    config:
      - name: Ethernet1/1
        description: 'Configured by Ansible'
        enable: True
      - name: Ethernet1/2
        description: 'Configured by Ansible'
        enable: False
    operation: merge

"""

RETURN = """
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nxos.config.interfaces.interfaces import Interface


def main():
    """ main entry point for module execution
    """
    module = AnsibleModule(argument_spec=Interface.argument_spec,
                           supports_check_mode=True)

    result = Interface(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
