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
from tobiko.openstack import neutron
from tobiko.openstack import stacks


class NetworkTestCase(testtools.TestCase):
    """Tests network creation"""

    #: Stack of resources with a network with a gateway router
    stack = tobiko.required_setup_fixture(stacks.NetworkStackFixture)

    @neutron.skip_if_missing_networking_extensions('port-security')
    def test_port_security_enabled(self):
        self.assertEqual(self.stack.port_security_enabled,
                         self.stack.network_details['port_security_enabled'])
        self.assertEqual(self.stack.port_security_enabled,
                         self.stack.outputs.port_security_enabled)

    @neutron.skip_if_missing_networking_extensions('net-mtu')
    def test_net_mtu(self):
        self.assertEqual(self.stack.network_details['mtu'],
                         self.stack.outputs.mtu)

    def test_ipv4_subnet_cidr(self):
        if not self.stack.has_ipv4:
            tobiko.skip('Stack {!s} has no ipv4 subnet', self.stack.stack_name)

        subnet = neutron.find_subnet(cidr=str(self.stack.ipv4_subnet_cidr))
        self.assertEqual(neutron.get_subnet(self.stack.ipv4_subnet_id), subnet)

    def test_ipv6_subnet_cidr(self):
        if not self.stack.has_ipv6:
            tobiko.skip('Stack {!s} has no ipv6 subnet', self.stack.stack_name)
        subnet = neutron.find_subnet(cidr=str(self.stack.ipv6_subnet_cidr))
        self.assertEqual(neutron.get_subnet(self.stack.ipv6_subnet_id), subnet)

    def test_gateway_network(self):
        if not self.stack.has_gateway:
            tobiko.skip('Stack {!s} has no gateway',
                        self.stack.stack_name)
        self.assertEqual(
            self.stack.gateway_network_id,
            self.stack.gateway_details['external_gateway_info']['network_id'])

    def test_ipv4_subnet_gateway_ip(self):
        if not self.stack.has_ipv4 or not self.stack.has_gateway:
            tobiko.skip('Stack {!s} has no IPv4 gateway',
                        self.stack.stack_name)
        self.assertIn(
            self.stack.ipv4_subnet_gateway_ip,
            self.stack.ipv4_gateway_addresses)

    def test_ipv6_subnet_gateway_ip(self):
        if not self.stack.has_ipv6 or not self.stack.has_gateway:
            tobiko.skip('Stack {!s} has no IPv6 gateway',
                        self.stack.stack_name)
        self.assertIn(
            self.stack.ipv6_subnet_gateway_ip,
            self.stack.ipv6_gateway_addresses)


@neutron.skip_if_missing_networking_extensions('net-mtu-write')
class NetworkWithNetMtuWriteTestCase(NetworkTestCase):

    #: Stack of resources with a network with a gateway router
    stack = tobiko.required_setup_fixture(
        stacks.NetworkWithNetMtuWriteStackFixture)

    def test_net_mtu_write(self):
        self.assertEqual(self.stack.mtu, self.stack.outputs.mtu)


@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class L3HaNetworkTestCase(NetworkTestCase):

    #: Stack of resources with a network with a gateway router
    stack = tobiko.required_setup_fixture(stacks.L3haNetworkStackFixture)
