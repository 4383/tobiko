# Copyright (c) 2019 Red Hat
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
from tobiko import config
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.openstack import neutron
from tobiko.openstack import stacks


CONF = config.CONF


class FloatingIPTest(testtools.TestCase):
    """Tests connectivity via floating IPs"""

    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def test_stack_create_complete(self):
        self.stack.key_pair_stack.wait_for_create_complete()
        self.stack.network_stack.wait_for_create_complete()
        self.stack.wait_for_create_complete()

    def test_ssh(self):
        """Test SSH connectivity to floating IP address"""
        hostname = sh.get_hostname(ssh_client=self.stack.ssh_client)
        self.assertEqual(self.stack.server_name.lower(), hostname)

    def test_ping(self):
        """Test ICMP connectivity to floating IP address"""
        ping.ping_until_received(
            self.stack.floating_ip_address).assert_replied()

    # --- test port-security extension ---------------------------------------

    @neutron.skip_if_missing_networking_extensions('port-security')
    def test_port_security_enabled_port_attribute(self):
        """Test port security enabled port attribute"""
        self.assertEqual(self.expected_port_security_enabled,
                         self.observed_port_security_enabled)

    @property
    def expected_port_security_enabled(self):
        """Expected port security enabled value"""
        return self.stack.port_security_enabled

    @property
    def observed_port_security_enabled(self):
        """Actual MTU value for internal network"""
        return self.stack.outputs.port_security_enabled

    # --- test security_group extension --------------------------------------

    @neutron.skip_if_missing_networking_extensions('security-group')
    def test_security_groups_port_attribute(self):
        """Test security groups port attribute"""
        self.assertEqual(self.expected_security_groups,
                         self.observed_security_groups)

    @property
    def expected_security_groups(self):
        """Expected port security groups"""
        return set(self.stack.security_groups)

    @property
    def observed_security_groups(self):
        """Actual port security group"""
        return set(self.stack.outputs.security_groups)

    # --- test net-mtu and net-mtu-writable extensions ------------------------

    @ping.skip_if_missing_fragment_ping_option
    @neutron.skip_if_missing_networking_extensions('net-mtu')
    def test_ping_with_net_mtu(self):
        """Test connectivity to floating IP address with MTU sized packets"""
        # Wait until it can reach remote port with maximum-sized packets
        ping.ping(self.stack.floating_ip_address,
                  until=ping.RECEIVED,
                  packet_size=self.observed_net_mtu,
                  fragmentation=False).assert_replied()

        # Verify it can't reach remote port with over-sized packets
        ping.ping(self.stack.floating_ip_address,
                  packet_size=self.observed_net_mtu + 1,
                  fragmentation=False,
                  count=5,
                  check=False).assert_not_replied()

    @property
    def observed_net_mtu(self):
        """Actual MTU value for internal network"""
        return self.stack.network_stack.outputs.mtu

    # --- test l3_ha extension ------------------------------------------------

    @neutron.skip_if_missing_networking_extensions('l3-ha')
    def test_l3_ha(self):
        """Test 'mtu' network attribute"""
        gateway = self.stack.network_stack.gateway_details
        self.assertEqual(self.stack.network_stack.ha,
                         gateway['ha'])


# --- Test with port security enabled -----------------------------------------

@neutron.skip_if_missing_networking_extensions('port-security',
                                               'security-group')
class FloatingIPWithPortSecurityFixture(stacks.CirrosServerStackFixture):
    """Heat stack for testing a floating IP instance with port security"""

    #: Resources stack with security group to allow ping Nova servers
    security_groups_stack = tobiko.required_setup_fixture(
        stacks.SecurityGroupsFixture)

    #: Enable port security on internal network
    port_security_enabled = True

    @property
    def security_groups(self):
        """List with ICMP security group"""
        return [self.security_groups_stack.ssh_security_group_id]


@neutron.skip_if_missing_networking_extensions('port-security',
                                               'security-group')
class FloatingIPWithPortSecurityTest(FloatingIPTest):
    """Tests connectivity via floating IPs with port security"""

    #: Resources stack with floating IP and Nova server with port security
    stack = tobiko.required_setup_fixture(FloatingIPWithPortSecurityFixture)

    def test_ping(self):
        """Test connectivity to floating IP address"""
        # Wait for server instance to get ready by logging in
        self.stack.ssh_client.connect()

        # Check can't reach secured port via floating IP
        ping.ping(self.stack.floating_ip_address,
                  count=5,
                  check=False).assert_not_replied()

    @ping.skip_if_missing_fragment_ping_option
    @neutron.skip_if_missing_networking_extensions('net-mtu')
    def test_ping_with_net_mtu(self):
        """Test connectivity to floating IP address"""
        # Wait for server instance to get ready by logging in
        tobiko.setup_fixture(self.stack.ssh_client)
        self.stack.ssh_client.connect()

        # Verify it can't reach secured port with maximum-sized packets
        ping.ping(self.stack.floating_ip_address,
                  packet_size=self.observed_net_mtu,
                  fragmentation=False,
                  count=5,
                  check=False).assert_not_replied()

        # Verify it can't reach secured port with over-sized packets
        ping.ping(self.stack.floating_ip_address,
                  packet_size=self.observed_net_mtu + 1,
                  fragmentation=False,
                  count=5,
                  check=False).assert_not_replied()


# --- Test with ICMP security group -------------------------------------------

class FloatingIPWithICMPSecurityGroupFixture(
        FloatingIPWithPortSecurityFixture):
    """Heat stack for testing a floating IP instance with security groups"""

    @property
    def security_groups(self):
        """List with ICMP security group"""
        return [self.security_groups_stack.ssh_security_group_id,
                self.security_groups_stack.icmp_security_group_id]


@neutron.skip_if_missing_networking_extensions('port-security',
                                               'security-group')
class FloatingIPWithICMPSecurityGroupTest(FloatingIPTest):
    """Tests connectivity via floating IP with security ICMP security group"""
    #: Resources stack with floating IP and Nova server to ping
    stack = tobiko.required_setup_fixture(
        FloatingIPWithICMPSecurityGroupFixture)


# --- Test net-mtu-write extension --------------------------------------------

@neutron.skip_if_missing_networking_extensions('net-mtu-writable')
class FloatingIPWithNetMtuWritableFixture(stacks.CirrosServerStackFixture):
    """Heat stack for testing floating IP with a custom MTU network value"""

    #: Heat stack for creating internal network with custom MTU value
    network_stack = tobiko.required_setup_fixture(
        stacks.NetworkWithNetMtuWriteStackFixture)


@neutron.skip_if_missing_networking_extensions('net-mtu-writable')
class FloatingIpWithMtuWritableTest(FloatingIPTest):
    """Tests connectivity via floating IP with a custom MTU value"""

    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(FloatingIPWithNetMtuWritableFixture)

    def test_net_mtu_write(self):
        """Test 'mtu' network attribute"""
        self.assertEqual(self.expected_net_mtu, self.observed_net_mtu)

    @property
    def expected_net_mtu(self):
        """Expected MTU value for internal network"""
        return self.stack.network_stack.custom_mtu_size


# --- Test la-h3 extension ----------------------------------------------------

@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class FloatingIpWithL3HATest(FloatingIPTest):
    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(stacks.L3haServerStackFixture)
