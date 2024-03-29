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

import time

from oslo_log import log


import tobiko
from tobiko.shell import sh
from tobiko.shell.ping import _interface
from tobiko.shell.ping import _exception
from tobiko.shell.ping import _parameters
from tobiko.shell.ping import _statistics


LOG = log.getLogger(__name__)


TRANSMITTED = 'transmitted'
DELIVERED = 'delivered'
UNDELIVERED = 'undelivered'
RECEIVED = 'received'
UNRECEIVED = 'unreceived'


def list_reachable_hosts(hosts, **params):
    reachable_host, _ = ping_hosts(hosts, **params)
    return reachable_host


def list_unreachable_hosts(hosts, **params):
    _, unreachable_host = ping_hosts(hosts, **params)
    return unreachable_host


def ping_hosts(hosts, **params):
    reachable = tobiko.Selection()
    unreachable = tobiko.Selection()
    for host in hosts:
        try:
            result = ping(host, count=1, **params)
        except _exception.PingError:
            LOG.exception('Error pinging host: %r', host)
            unreachable.append(host)
        else:
            if result.received:
                reachable.append(host)
            else:
                unreachable.append(host)
    return reachable, unreachable


def ping(host, until=TRANSMITTED, check=True, **ping_params):
    """Send ICMP messages to host address until timeout

    :param host: destination host address
    :param **ping_params: parameters to be forwarded to get_statistics()
        function
    :returns: PingStatistics
    """
    return get_statistics(host=host, until=until, check=check, **ping_params)


def ping_until_delivered(host, **ping_params):
    """Send 'count' ICMP messages

    Send 'count' ICMP messages

    ICMP messages are considered delivered when they have been
    transmitted without being counted as errors.

    :param host: destination host address
    :param **ping_params: parameters to be forwarded to get_statistics()
        function
    :returns: PingStatistics
    :raises: PingFailed in case timeout expires before delivering all
        expected count messages
    """
    return ping(host=host, until=DELIVERED, **ping_params)


def ping_until_undelivered(host, **ping_params):
    """Send ICMP messages until it fails to deliver messages

    Send ICMP messages until it fails to deliver 'count' messages

    ICMP messages are considered undelivered when they have been
    transmitted and they have been counted as error in ping statistics (for
    example because of errors into the route to remote address).

    :param host: destination host address
    :param **ping_params: parameters to be forwarded to get_statistics()
        function
    :returns: PingStatistics
    :raises: PingFailed in case timeout expires before failing delivering
        expected 'count' of messages
    """
    return ping(host=host, until=UNDELIVERED, **ping_params)


def ping_until_received(host, **ping_params):
    """Send ICMP messages until it receives messages back

    Send ICMP messages until it receives 'count' messages back

    ICMP messages are considered received when they have been
    transmitted without any routing errors and they are received back

    :param host: destination host address
    :param **ping_params: parameters to be forwarded to get_statistics()
        function
    :returns: PingStatistics
    :raises: PingFailed in case timeout expires before receiving all
        expected 'count' of messages
    """
    return ping(host=host, until=RECEIVED, **ping_params)


def ping_until_unreceived(host, **ping_params):
    """Send ICMP messages until it fails to receive messages

    Send ICMP messages until it fails to receive 'count' messages back.

    ICMP messages are considered unreceived when they have been
    transmitted without any routing error but they failed to be received
    back (for example because of network filtering).

    :param host: destination host address
    :param **ping_params: parameters to be forwarded to get_statistics()
        function
    :returns: PingStatistics
    :raises: PingFailed in case timeout expires before failed receiving
        expected 'count' of messages
    """
    return ping(host=host, until=UNRECEIVED, **ping_params)


def get_statistics(parameters=None, ssh_client=None, until=None, check=True,
                   **ping_params):
    parameters = _parameters.get_ping_parameters(default=parameters,
                                                 **ping_params)
    statistics = _statistics.PingStatistics()
    for partial_statistics in iter_statistics(parameters=parameters,
                                              ssh_client=ssh_client,
                                              until=until, check=check):
        statistics += partial_statistics
        LOG.debug("%r", statistics)

    return statistics


def iter_statistics(parameters=None, ssh_client=None, until=None, check=True,
                    **ping_params):
    parameters = _parameters.get_ping_parameters(default=parameters,
                                                 **ping_params)
    now = time.time()
    end_of_time = now + parameters.timeout
    deadline = parameters.deadline
    transmitted = 0
    received = 0
    undelivered = 0
    count = 0
    enlapsed_time = None

    while deadline > 0. and count < parameters.count:
        if enlapsed_time is not None and enlapsed_time < deadline:
            # Avoid busy waiting when errors happens
            sleep_time = deadline - enlapsed_time
            LOG.debug('Waiting %s seconds before next ping execution',
                      sleep_time)
            time.sleep(sleep_time)

        start_time = time.time()

        # splitting total timeout interval into smaller deadline intervals will
        # cause ping command to be executed more times allowing to handle
        # temporary packets routing problems
        if until == RECEIVED:
            execute_parameters = _parameters.get_ping_parameters(
                default=parameters,
                deadline=deadline,
                count=(parameters.count - count),
                timeout=end_of_time - now)
        else:
            # Deadline ping parameter cause ping to be executed until count
            # messages are received or deadline is expired
            # Therefore to count messages not of received type we have to
            # simulate deadline parameter limiting the maximum number of
            # transmitted messages
            execute_parameters = _parameters.get_ping_parameters(
                default=parameters,
                deadline=deadline,
                count=min(parameters.count - count,
                          parameters.interval * deadline),
                timeout=end_of_time - now)

        # Command timeout would typically give ping command additional seconds
        # to safely reach deadline before shell command timeout expires, while
        # in the same time adding an extra verification to forbid using more
        # time than expected considering the time required to make SSH
        # connection and running a remote shell
        output = execute_ping(parameters=execute_parameters,
                              ssh_client=ssh_client,
                              check=check)

        if output:
            statistics = _statistics.parse_ping_statistics(
                output=output, begin_interval=now,
                end_interval=time.time())

            yield statistics

            transmitted += statistics.transmitted
            received += statistics.received
            undelivered += statistics.undelivered
        else:
            # Assume 1 transmitted undelivered package when unable to get
            # ping output
            transmitted += 1
            undelivered += 1

        count = {None: 0,
                 TRANSMITTED: transmitted,
                 DELIVERED: transmitted - undelivered,
                 UNDELIVERED: undelivered,
                 RECEIVED: received,
                 UNRECEIVED: transmitted - received}[until]

        now = time.time()
        deadline = min(int(end_of_time - now), parameters.deadline)
        enlapsed_time = now - start_time
        if enlapsed_time > 0.:
            LOG.debug('Ping execution took %s seconds', enlapsed_time)

    if until and count < parameters.count:
        raise _exception.PingFailed(count=count,
                                    expected_count=parameters.count,
                                    timeout=parameters.timeout,
                                    message_type=until)


def execute_ping(parameters, ssh_client=None, check=True):
    command = _interface.get_ping_command(parameters=parameters,
                                          ssh_client=ssh_client)

    try:
        result = sh.execute(command=command,
                            ssh_client=ssh_client,
                            timeout=parameters.deadline + 2.,
                            expect_exit_status=None,
                            network_namespace=parameters.network_namespace)
    except sh.ShellError as ex:
        LOG.exception("Error executing ping command")
        stdout = ex.stdout
        stderr = ex.stderr
    else:
        stdout = result.stdout
        stderr = result.stderr

    if stdout:
        output = str(stdout)
        LOG.debug('Received ping STDOUT:\n%s', output)
    else:
        output = None

    if stderr:
        error = str(stderr)
        LOG.info('Received ping STDERR:\n%s', error)
        if check and result.exit_status:
            handle_ping_command_error(error=error)

    return output


def handle_ping_command_error(error):
    for error in error.splitlines():
        error = error.strip()
        if error:
            prefix = 'ping: '
            if error.startswith('ping: '):
                text = error[len(prefix):]

                prefix = 'bad address '
                if text.startswith(prefix):
                    address = text[len(prefix):].replace("'", '').strip()
                    raise _exception.BadAddressPingError(address=address)

                prefix = 'local error: '
                if text.startswith(prefix):
                    details = text[len(prefix):].strip()
                    raise _exception.LocalPingError(details=details)

                prefix = 'sendto: '
                if text.startswith(prefix):
                    details = text[len(prefix):].strip()
                    raise _exception.SendToPingError(details=details)

                prefix = 'unknown host'
                if text.startswith(prefix):
                    details = text[len(prefix):].strip()
                    raise _exception.UnknowHostError(details=details)

                suffix = ': Name or service not known'
                if text.endswith(suffix):
                    details = text[:-len(suffix)].strip()
                    raise _exception.UnknowHostError(details=details)

                suffix = ': No route to host'
                if text.endswith(suffix):
                    details = text[:-len(suffix)].strip()
                    raise _exception.UnknowHostError(details=details)

                raise _exception.PingError(details=text)
