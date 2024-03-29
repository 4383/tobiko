# Copyright 2019 Red Hat
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

from tobiko.openstack.keystone import _client
from tobiko.openstack.keystone import _clouds_file
from tobiko.openstack.keystone import _credentials
from tobiko.openstack.keystone import _services
from tobiko.openstack.keystone import _session

keystone_client = _client.keystone_client
get_keystone_client = _client.get_keystone_client
find_service = _client.find_service
find_endpoint = _client.find_endpoint
find_service_endpoint = _client.find_service_endpoint
list_endpoints = _client.list_endpoints
list_services = _client.list_services
KeystoneClientFixture = _client.KeystoneClientFixture

CloudsFileKeystoneCredentialsFixture = (
    _clouds_file.CloudsFileKeystoneCredentialsFixture)

keystone_credentials = _credentials.keystone_credentials
get_keystone_credentials = _credentials.get_keystone_credentials
default_keystone_credentials = _credentials.default_keystone_credentials
KeystoneCredentials = _credentials.KeystoneCredentials
KeystoneCredentialsFixture = _credentials.KeystoneCredentialsFixture
EnvironKeystoneCredentialsFixture = \
    _credentials.EnvironKeystoneCredentialsFixture
InvalidKeystoneCredentials = _credentials.InvalidKeystoneCredentials
DEFAULT_KEYSTONE_CREDENTIALS_FIXTURES = \
    _credentials.DEFAULT_KEYSTONE_CREDENTIALS_FIXTURES

has_service = _services.has_service
is_service_missing = _services.is_service_missing
skip_if_missing_service = _services.skip_if_missing_service

keystone_session = _session.keystone_session
KeystoneSessionFixture = _session.KeystoneSessionFixture
KeystoneSessionManager = _session.KeystoneSessionManager
get_keystone_session = _session.get_keystone_session
