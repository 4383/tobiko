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

import podman

import tobiko
from tobiko.docker import _exception
from tobiko.docker import _shell
from tobiko.shell import ssh


def get_podman_client(base_urls=None, ssh_client=None):
    return PodmanClientFixture(base_urls=base_urls,
                               ssh_client=ssh_client)


def list_podman_containers(client=None, **kwargs):
    try:
        containers = podman_client(client).containers.list(**kwargs)
    except _exception.DockerUrlNotFoundError:
        return tobiko.Selection()
    else:
        return tobiko.select(containers)


def docker_client(obj=None):
    if obj is None:
        obj = get_docker_client()
    if tobiko.is_fixture(obj):
        obj = tobiko.setup_fixture(obj).client
    if isinstance(obj, docker.DockerClient):
        return obj
    raise TypeError('Cannot obtain a DockerClient from {!r}'.format(obj))


class DockerClientFixture(tobiko.SharedFixture):

    base_urls = None
    client = None
    ssh_client = None

    def __init__(self, base_urls=None, ssh_client=None):
        super(DockerClientFixture, self).__init__()
        if base_urls:
            self.base_urls = list(base_urls)
        if ssh_client:
            self.ssh_client = ssh_client

    def setup_fixture(self):
        self.setup_ssh_client()
        self.setup_base_urls()
        self.setup_client()

    def setup_ssh_client(self):
        ssh_client = self.ssh_client
        if ssh_client is None:
            self.ssh_client = ssh_client = ssh.ssh_proxy_client() or False
            if ssh_client:
                tobiko.setup_fixture(ssh_client)
        return ssh_client

    def setup_base_urls(self):
        base_urls = self.base_urls
        if base_urls is None:
            self.base_urls = base_urls = self.discover_docker_urls()
        return base_urls

    def setup_client(self):
        client = self.client
        if client is None:
            self.client = client = self.create_client()
        return client

    def create_client(self):
        exc_info = None
        for base_url in self.base_urls:
            if self.ssh_client:
                base_url = ssh.get_port_forward_url(ssh_client=self.ssh_client,
                                                    url=base_url)
            client = docker.DockerClient(base_url=base_url)
            try:
                client.ping()
            except Exception:
                exc_info = exc_info or tobiko.exc_info()
            else:
                return client

        if exc_info:
            exc_info.reraise()
        else:
            raise _exception.DockerError('Unable to create docker client')

    def connect(self):
        return tobiko.setup_fixture(self).client

    def discover_docker_urls(self):
        return _shell.discover_docker_urls(ssh_client=self.ssh_client)
