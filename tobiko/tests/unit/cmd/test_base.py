# Copyright (c) 2018 Red Hat
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import absolute_import

import sys

from tobiko.cmd import base
from tobiko.tests.unit import openstack


class TobikoCMDTest(openstack.OpenstackTest):

    command_name = 'tobiko-base'
    command_class = base.TobikoCMD

    def test_init(self, argv=None):
        self.patch_argv(argv=argv)
        return self.command_class()

    def patch_argv(self, argv=None):
        return self.patch(sys, 'argv', [self.command_name] + (argv or []))
