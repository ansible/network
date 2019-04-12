#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 <company_name>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
################# WARNING ####################
##############################################
###
### This file is auto generated by the resource
###   module builder playbook.
###
### Do not edit this file manually.
###
### Changes to this file will be over written
###   by the resource module builder.
###
### Changes should be made in the model used to
###   generate this file or in the resource module
###   builder template.
###
##############################################
##############################################
##############################################
"""
The arg spec for the myos_interfaces module
"""

class InterfacesArgs(object): #pylint: disable=R0903
    """The arg spec for the myos_interfaces module
    """

    def __init__(self, **kwargs):
        pass

    config_spec = {
        'name': dict(type='str', required=True),
        'description': dict(),
        'enabled': dict(default=True, type=bool),
        'speed': dict(),
        'mtu': dict(),
        'duplex': dict(choices=['full', 'half']),
    }

    argument_spec = {
        'state': dict(default='merged', choices=['merged', 'replaced', 'overriden', 'deleted']),
        'config': dict(type='list', elements='dict', options=config_spec)
    }