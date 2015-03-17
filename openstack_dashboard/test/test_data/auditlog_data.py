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

from auditlogclient.v1 import auditlogs

from openstack_dashboard.test.test_data import utils


def data(TEST):
    TEST.auditlogs = utils.TestDataContainer()

    auditlog_dict = {'id': '007e7d55-fe1e-4c5c-bf08-44b4a4964822',
                  'user_id': '1',
                  'tenant_id': "1",
                  'path': "neutron/ip",
                  'rid': '1.1',
                  'method': "GET",
                  'status_code': "200",
                  'begin_at': "2013-01-01T00:00:00",
                  'end_at': "2013-01-01T00:00:00"}
    auditlog1 = auditlogs.Auditlog(auditlogs.AuditlogManager(None),
                  auditlog_dict)

    auditlog_dict = {'id': '278905a6-4b52-4d1e-98f9-8c57bb25ba32',
                  'user_id': '1',
                  'tenant_id': "1",
                  'path': "neutron/ip_float",
                  'rid': '1.2',
                  'method': "DELETE",
                  'status_code': "200",
                  'begin_at': "2014-01-01T00:00:00",
                  'end_at': "2014-01-01T00:00:00"}
    auditlog2 = auditlogs.Auditlog(auditlogs.AuditlogManager(None),
                  auditlog_dict)

    auditlog_dict = {'id': '7cd892fd-5652-40f3-a450-547615680132',
                  'user_id': '1',
                  'tenant_id': "1",
                  'path': "neutron/ip_float",
                  'rid': '1.2',
                  'method': "DELETE",
                  'status_code': "200",
                  'begin_at': "2014-01-01T00:00:00",
                  'end_at': "2014-01-01T00:00:00"}
    auditlog3 = auditlogs.Auditlog(auditlogs.AuditlogManager(None),
                  auditlog_dict)

    auditlog_dict = {'id': 'c8756975-7a3b-4e43-b7f7-433576112849',
                  'user_id': '1',
                  'tenant_id': "1",
                  'path': "neutron/ip_float",
                  'rid': '1.2',
                  'method': "DELETE",
                  'status_code': "200",
                  'begin_at': "2014-01-01T00:00:00",
                  'end_at': "2014-01-01T00:00:00"}
    auditlog4 = auditlogs.Auditlog(auditlogs.AuditlogManager(None),
                  auditlog_dict)

    auditlog_dict = {'id': 'f448704f-0ce5-4d34-8441-11b6581c6619',
                  'user_id': '1',
                  'tenant_id': "1",
                  'path': "neutron/ip_float",
                  'rid': '1.2',
                  'method': "DELETE",
                  'status_code': "200",
                  'begin_at': "2014-01-01T00:00:00",
                  'end_at': "2014-01-01T00:00:00"}
    auditlog5 = auditlogs.Auditlog(auditlogs.AuditlogManager(None),
                  auditlog_dict)

    auditlog_dict = {'id': 'a67e7d45-fe1e-4c5c-bf08-44b4a4964822',
                  'user_id': '1',
                  'tenant_id': "1",
                  'path': "neutron/ip_float",
                  'rid': '1.2',
                  'method': "DELETE",
                  'status_code': "200",
                  'begin_at': "2014-01-01T00:00:00",
                  'end_at': "2014-01-01T00:00:00"}
    auditlog6 = auditlogs.Auditlog(auditlogs.AuditlogManager(None),
                  auditlog_dict)

    TEST.auditlogs.add(auditlog1, auditlog2, auditlog3,
                    auditlog4, auditlog5, auditlog6)

#    TEST.resources = utils.TestDataContainer()
#    resource1 = {'rid': '1.1', 'name': 'IP'}
#    resource2 = {'rid': '1.2', 'name': 'Floating IP'}
#    TEST.resources.add(resource1, resource2)
