# Copyright (c) 2019 Red Hat, Inc.
#
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

import testtools

import tobiko
from tobiko.openstack import stacks
from tobiko.shell import ping
from tobiko.shell import sh


class FloatingIpServerTest(testtools.TestCase):
    """Tests connectivity to Nova instances via floating IPs"""

    stack = tobiko.required_setup_fixture(
        stacks.FloatingIpServerStackFixture)

    @property
    def floating_ip_address(self):
        """Floating IP address"""
        return self.stack.outputs.floating_ip_address

    @property
    def ssh_client(self):
        """Floating IP address"""
        return self.stack.ssh_client

    @property
    def server_name(self):
        """Floating IP address"""
        return self.stack.outputs.server_name

    def test_ping(self):
        """Test connectivity to floating IP address"""
        ping.ping_until_received(self.floating_ip_address).assert_replied()

    def test_hostname(self):
        """Test that hostname of instance server matches Nova server name"""
        result = sh.execute('hostname', ssh_client=self.ssh_client)
        hostname, = str(result.stdout).splitlines()
        self.assertEqual(hostname, self.server_name)