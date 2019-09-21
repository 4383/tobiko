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

from oslo_log import log


LOG = log.getLogger(__name__)


def makedirs(name, mode=0o777, exist_ok=True):
    """Creates directory and its parents if directory doesn't exists.

    This emulates Python3 os.makedirs behavior[1]

    [1] https://docs.python.org/3/library/os.html#os.makedirs)
    """
    try:
        os.makedirs(name, mode)
    except Exception:
        if not exist_ok or not os.path.isdir(name):
            raise