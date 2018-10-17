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
from tobiko.tests.scenario import base
from tobiko.common.asserts import assert_ping


class FloatingIPTest(base.ScenarioTestsBase):
    """Tests server connectivity"""

    def test_pre_fip(self):
        """Validates connectivity to a server created by another test."""

        fip = self.stackManager.get_output("scenario")
        assert_ping(fip)

    def test_post_fip(self):
        """Validates connectivity to a server post upgrade."""

        fip = self.stackManager.get_output("scenario")
        assert_ping(fip)
