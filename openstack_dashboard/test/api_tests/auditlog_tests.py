# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from django.conf import settings
from django.test.utils import override_settings

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class AuditlogApiTests(test.APITestCase):
    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_auditlog_list_no_pagination(self):
        api_auditlogs = self.auditlogs.list()
        filters = {}
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        auditlogclient = self.stub_auditlogclient()
        auditlogclient.auditlog = self.mox.CreateMockAnything()
        auditlogclient.auditlog.list(page_size=limit,
                             limit=limit,
                             q=filters,).AndReturn(iter(api_auditlogs))
        self.mox.ReplayAll()

        auditlogs, has_more = api.auditlog.auditlog_list(self.request)
        self.assertItemsEqual(auditlogs, api_auditlogs)
        self.assertFalse(has_more)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_auditlog_list_pagination(self):
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        api_auditlogs = self.auditlogs.list()
        auditlog_iter = iter(api_auditlogs)

        auditlogclient = self.stub_auditlogclient()
        auditlogclient.auditlog = self.mox.CreateMockAnything()
        auditlogclient.auditlog.list(limit=limit,
                                 page_size=page_size + 1,
                                 q=filters,).AndReturn(auditlog_iter)
        self.mox.ReplayAll()

        auditlogs, has_more = api.auditlog.auditlog_list(self.request,
                                                          marker=None,
                                                          q=filters,
                                                          paginate=True)
        expected_auditlogs = api_auditlogs[:page_size]
        self.assertItemsEqual(auditlogs, expected_auditlogs)
        self.assertTrue(has_more)
        self.assertEqual(len(list(auditlog_iter)),
                         len(api_auditlogs) - len(expected_auditlogs) - 1)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_auditlog_list_pagination_marker(self):
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
        marker = 'nonsense'

        api_auditlogs = self.auditlogs.list()[page_size:]
        auditlog_iter = iter(api_auditlogs)

        auditlogclient = self.stub_auditlogclient()
        auditlogclient.auditlog = self.mox.CreateMockAnything()
        auditlogclient.auditlog.list(limit=limit,
                                 page_size=page_size + 1,
                                 q=filters,
                                 marker=marker).AndReturn(auditlog_iter)
        self.mox.ReplayAll()

        auditlogs, has_more = api.auditlog.auditlog_list(self.request,
                                                          marker=marker,
                                                          q=filters,
                                                          paginate=True)
        expected_auditlogs = api_auditlogs[:page_size]
        self.assertItemsEqual(auditlogs, expected_auditlogs)
        self.assertTrue(has_more)
        self.assertEqual(len(list(auditlog_iter)),
                         len(api_auditlogs) - len(expected_auditlogs) - 1)
