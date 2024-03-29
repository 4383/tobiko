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

import os
import typing  # noqa

import jinja2
import six

from oslo_log import log

import tobiko
from tobiko.openstack.os_faults import _exception
from tobiko.openstack import topology
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


def get_os_fault_config_filename():
    return tobiko.setup_fixture(OsFaultsConfigFileFixture).config_filename


class OsFaultsConfigFileFixture(tobiko.SharedFixture):
    """Responsible for managing faults configuration."""

    config = None
    config_filename = None
    template_filename = None
    topo = None

    def __init__(self, config=None, config_filename=None,
                 template_filename=None, topo=None):
        super(OsFaultsConfigFileFixture, self).__init__()
        self.templates_dir = os.path.join(os.path.dirname(__file__),
                                          'templates')
        if config is not None:
            self.config = config
        if config_filename is not None:
            self.config_filename = config_filename
        if template_filename is not None:
            self.template_filename = template_filename
        if topo:
            self.topo = topo

    def setup_fixture(self):
        _config = self.config
        if not _config:
            from tobiko import config
            CONF = config.CONF
            self.config = _config = CONF.tobiko.os_faults
        self.config_filename = config_filename = self.get_config_filename()
        if config_filename is None:
            self.config_filename = self.generate_config_file(
                config_filename=config_filename)

    def get_config_filename(self):
        config_filename = self.config_filename
        if config_filename is None:
            config_filename = os.environ.get('OS_FAULTS_CONFIG') or None

        if config_filename is None:
            config_dirnames = self.config.config_dirnames
            config_filenames = self.config.config_filenames
            for dirname in config_dirnames:
                dirname = os.path.realpath(os.path.expanduser(dirname))
                for filename in config_filenames:
                    filename = os.path.join(dirname, filename)
                    if os.path.isfile(filename):
                        config_filename = filename
                        break

        if config_filename is None:
            LOG.warning("Unable to find any of 'os_faults' files (%s) in "
                        "any directory (%s",
                        ', '.join(config_filenames),
                        ', '.join(config_dirnames))
        return config_filename

    def get_template_filename(self):
        template_filename = self.template_filename
        if template_filename is None:
            template_filename = os.environ.get('OS_FAULTS_TEMPLATE') or None

        if template_filename is None:
            template_dirnames = self.config.template_dirnames
            config_filenames = self.config.config_filenames
            template_filenames = [filename + '.j2'
                                  for filename in config_filenames]
            for dirname in template_dirnames:
                dirname = os.path.realpath(os.path.expanduser(dirname))
                for filename in template_filenames:
                    filename = os.path.join(dirname, filename)
                    if os.path.isfile(filename):
                        template_filename = filename
                        break

        if template_filename is None:
            LOG.warning("Unable to find any of 'os_faults' template file "
                        "(%s) in any directory (%s").format(
                            ', '.join(template_filenames),
                            ', '.join(template_dirnames))
        return template_filename

    def generate_config_file(self, config_filename):
        """Generates os-faults configuration file."""

        self.template_filename = template_filename = (
            self.get_template_filename())
        template_basename = os.path.basename(template_filename)
        if config_filename is None:
            config_dirname = os.path.realpath(
                os.path.expanduser(self.config.generate_config_dirname))
            config_basename, template_ext = os.path.splitext(template_basename)
            assert template_ext == '.j2'
            config_filename = os.path.join(config_dirname, config_basename)
        else:
            config_dirname = os.path.dirname(config_filename)

        LOG.info("Generating os-fault config file from template %r to %r.",
                 template_filename, config_filename)
        tobiko.makedirs(config_dirname)

        make_os_faults_config_file(config_filename=config_filename,
                                   template_filename=template_filename,
                                   topo=self.topo)
        return config_filename


def make_os_faults_config_file(config_filename, template_filename, topo=None):
    # type: (str, str, topology.OpenStackTopology) -> int
    template = get_os_faults_config_template(template_filename)
    config_content = get_os_faults_config_content(template=template, topo=topo)
    with tobiko.open_output_file(config_filename) as stream:
        LOG.debug('Write os-foults config file to %r:\n%s', config_filename,
                  config_content)
        return stream.write(config_content)


def get_os_faults_config_template(filename):
    # type: (str) -> jinja2.Template
    basename = os.path.basename(filename)
    dirname = os.path.dirname(filename)
    loader = jinja2.FileSystemLoader(dirname)
    environment = jinja2.Environment(loader=loader, trim_blocks=True)
    return environment.get_template(basename)


def get_os_faults_config_content(template, topo=None):
    # type: (jinja2.Template, topology.OpenStackTopology) -> typing.Text
    topo = topo or topology.get_openstack_topology()
    nodes = [get_os_faults_node_from_topology(node) for node in topo.nodes]
    # TODO: get services and containers from OpenStack topology
    services = []  # type: typing.List[str]
    containers = []  # type: typing.List[str]
    return template.render(nodes=nodes,
                           services=services,
                           containers=containers)


def get_os_faults_node_from_topology(node):
    # type: (topology.OpenStackTopologyNode) -> typing.Dict
    return {'fqdn': node.name,
            'ip': str(node.ssh_parameters['hostname']),
            'auth': get_os_faults_node_auth_from_topology(node)}


def get_os_faults_node_auth_from_topology(node):
    # type: (topology.OpenStackTopologyNode) -> typing.Dict
    private_key_file = get_os_faults_private_key_file(
        key_filename=node.ssh_parameters['key_filename'])
    port = int(node.ssh_parameters.get('port') or 22)
    if port != 22:
        LOG.warning('os-faults only support SSH port 22, but requiring %d for '
                    'node %r (%s)', port, node.name, node.public_ip)
    auth = {'username': node.ssh_parameters['username'],
            'private_key_file': private_key_file}
    jump = get_os_faults_node_auth_jump_from_topology(node)
    if jump:
        auth['jump'] = jump
    return auth


def get_os_faults_node_auth_jump_from_topology(node):
    # type: (topology.OpenStackTopologyNode) -> typing.Optional[typing.Dict]
    host_config = ssh.ssh_host_config(str(node.public_ip))
    if host_config.proxy_jump:
        proxy_config = ssh.ssh_host_config(host_config.proxy_jump)
        port = int(proxy_config.port or 22)
        if port != 22:
            LOG.warning('os-faults only support SSH port 22, but requiring %d '
                        'for proxy %r (%s)', port, host_config.proxy_jump,
                        proxy_config.hostname)
        private_key_file = get_os_faults_private_key_file(
            key_filename=proxy_config.key_filename)
        return {'host': proxy_config.hostname,
                'username': proxy_config.username,
                'private_key_file': private_key_file}
    else:
        return None


def get_os_faults_private_key_file(key_filename):
    # type: (typing.Union[str, typing.Sequence]) -> str

    if isinstance(key_filename, six.string_types):
        key_filename = [key_filename]
    else:
        key_filename = list(key_filename)
    for filename in key_filename:
        filename = os.path.expanduser(filename)
        if os.path.exists(filename):
            return os.path.expanduser(filename)
        else:
            LOG.warning('Private key file not found: %r', filename)
    raise _exception.NoSuchPrivateKeyFilename(
        key_filename=', '.join(key_filename))


def parse_config_node(node):
    # type: (str) -> typing.Dict
    fields = node.split('.')
    if len(fields) != 2:
        message = ("Invalid cloud node format: {!r} "
                   "(expected '<name>:<address>')").format(node)
        raise ValueError(message)
    return {'name': fields[0], 'address': fields[1]}
