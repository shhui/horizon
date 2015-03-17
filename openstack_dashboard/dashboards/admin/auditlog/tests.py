# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.core.urlresolvers import reverse
from django import http
from django.test.utils import override_settings

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class AuditlogsViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.auditlog: ('auditlog_list',
                                       'resource_list',),
                        api.keystone: ('tenant_list',
                                       'user_list',)})
    def test_auditlogs_list(self):
        # In form.__init__
        api.auditlog.resource_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        api.keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])
        api.keystone.user_list(IsA(http.HttpRequest)) \
            .AndReturn(self.users.list())
        # In view method
        api.auditlog.auditlog_list(IsA(http.HttpRequest),
                                   marker=None,
                                   paginate=True,
                                   q=IsA(list)) \
            .AndReturn([self.auditlogs.list(),
                        False])
        api.keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])
        api.keystone.user_list(IsA(http.HttpRequest)) \
            .AndReturn(self.users.list())
        api.auditlog.resource_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:admin:auditlog:index'))
        self.assertTemplateUsed(res, 'admin/auditlog/index.html')
        self.assertEqual(len(res.context['auditlog_table'].data),
                         len(self.auditlogs.list()))

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_stubs({api.auditlog: ('auditlog_list',
                                       'resource_list',),
                        api.keystone: ('tenant_list',
                                       'user_list',)})
    def test_auditlogs_list_get_pagination(self):
        auditlogs = self.auditlogs.list()[:5]
        # In form init
        api.auditlog.resource_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        api.keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])
        api.keystone.user_list(IsA(http.HttpRequest)) \
            .AndReturn(self.users.list())
        # In view method
        api.auditlog.auditlog_list(IsA(http.HttpRequest),
                                   marker=None,
                                   paginate=True,
                                   q=IsA(list)) \
            .AndReturn([auditlogs, True])
        api.keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])
        api.keystone.user_list(IsA(http.HttpRequest)) \
            .AndReturn(self.users.list())
        api.auditlog.resource_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        self.mox.ReplayAll()

        url = reverse('horizon:admin:auditlog:index')
        res = self.client.get(url)
        # get all
        self.assertEqual(len(res.context['auditlog_table'].data),
                         len(auditlogs))
        self.assertTemplateUsed(res, 'admin/auditlog/index.html')
        self.assertTrue(res.context['auditlog_table'].has_more_data())
