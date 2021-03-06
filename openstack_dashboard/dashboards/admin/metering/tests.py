# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import json
import uuid

from django.core.urlresolvers import reverse
from django import http
from mox import Func  # noqa
from mox import In    # noqa
from mox import IsA   # noqa

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.metering import tabs
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse("horizon:admin:metering:index")


class MeteringViewTests(test.APITestCase, test.BaseAdminViewTests):
    def test_stats_page(self):
        meters = self.meters.list()

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.meters = self.mox.CreateMockAnything()
        ceilometerclient.meters.list(None).AndReturn(meters)

        self.mox.ReplayAll()

        # getting all resources and with statistics
        res = self.client.get(reverse('horizon:admin:metering:index') +
            "?tab=ceilometer_overview__stats")
        self.assertTemplateUsed(res, 'admin/metering/index.html')
        self.assertTemplateUsed(res, 'admin/metering/stats.html')

    def test_report_page(self):
        # getting report page with no api access
        res = self.client.get(reverse('horizon:admin:metering:index') +
            "?tab=ceilometer_overview__daily_report")
        self.assertTemplateUsed(res, 'admin/metering/index.html')
        self.assertTemplateUsed(res, 'admin/metering/daily.html')

    def _verify_series(self, series, value, date, expected_names):
        expected_names.reverse()
        data = json.loads(series)
        self.assertTrue('series' in data)
        self.assertEqual(len(data['series']), len(expected_names))
        for d in data['series']:
            self.assertTrue('data' in d)
            self.assertEqual(len(d['data']), 1)
            self.assertAlmostEqual(d['data'][0].get('y'), value)
            self.assertEqual(d['data'][0].get('x'), date)
            self.assertEqual(d.get('name'), expected_names.pop())
            self.assertEqual(d.get('unit'), '')

        self.assertEqual(data.get('settings'), {})

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_stats_for_line_chart(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        # check that list is called twice for one resource and 2 meters
        ceilometerclient.statistics.list(meter_name="memory",
                                         period=IsA(int), q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # get all statistics of project aggregates
        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=memory&group_by=project&stats_attr=avg&date_options=7")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = ['test_tenant',
                          'disabled_tenant',
                          u'\u4e91\u89c4\u5219']
        self._verify_series(res._container[0], 4.55, '2012-12-21T11:00:55',
                            expected_names)

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_stats_for_line_chart_attr_max(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        # check that list is called twice for one resource and 2 meters
        ceilometerclient.statistics.list(meter_name="memory",
                                         period=IsA(int), q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # get all statistics of project aggregates
        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=memory&group_by=project&stats_attr=max&date_options=7")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = ['test_tenant',
                          'disabled_tenant',
                          u'\u4e91\u89c4\u5219']
        self._verify_series(res._container[0], 9.0, '2012-12-21T11:00:55',
                            expected_names)

    def test_stats_for_line_chart_no_group_by(self):
        resources = self.resources.list()
        statistics = self.statistics.list()

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.resources = self.mox.CreateMockAnything()
        ceilometerclient.resources.list(q=[]).AndReturn(resources)

        ceilometerclient.statistics = self.mox.CreateMockAnything()
        ceilometerclient.statistics.list(meter_name="storage.objects",
                                         period=IsA(int), q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # getting all resources and with statistics, I have only
        # 'storage.objects' defined in test data
        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=storage.objects&stats_attr=avg&date_options=7")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = ['fake_resource_id',
                          'fake_resource_id2']
        self._verify_series(res._container[0], 4.55, '2012-12-21T11:00:55',
                            expected_names)

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_stats_with_resource_id_filter(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        query = {'field': 'resource_id',
                  'op': 'eq',
                  'value': 'fake_resource_id'}
        # check that list is called twice for one resource and 3 tenants
        ceilometerclient.statistics.list(meter_name="instance",
                                         period=IsA(int), q=In(query)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # get resource(id='fake_resource_id') samples of project aggregates
        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=instance&group_by=project&date_options=null" +
            "&resource_id=fake_resource_id")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = ['instance',
                          'instance',
                          u'instance']
        self._verify_series(res._container[0], 4.55, '2012-12-21T11:00:55',
                            expected_names)

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_stats_with_date_options_null(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()

        # should query 8 hours ago samples from now
        def has_ts_filter(query):
            date_from = None
            date_to = None
            for each in query:
                if each['field'] == 'timestamp':
                    if each['op'] == 'ge':
                        date_from = each['value']
                    elif each['op'] == 'le':
                        date_to = each['value']

            if date_from is None or date_to is None:
                return False
            return (date_to - date_from).seconds == (8 * 3600)

        # check that list is called twice for one resource and 3 tenants
        ceilometerclient.statistics.list(meter_name="instance",
                                         period=IsA(int),
                                         q=Func(has_ts_filter)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # get 8 hours ago samples of project aggregates
        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=instance&group_by=project&date_options=null")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = ['test_tenant',
                          'disabled_tenant',
                          u'\u4e91\u89c4\u5219']
        self._verify_series(res._container[0], 4.55, '2012-12-21T11:00:55',
                            expected_names)

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_stats_with_resource_id_like_filter(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        query = {'field': 'resource_id',
                  'op': 'like',
                  'value': 'fake_resource_id%'}
        # check that list is called twice for one resource and 3 tenants
        ceilometerclient.statistics.list(meter_name="instance",
                                         period=IsA(int), q=In(query)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # get resource(id='fake_resource_id') samples of project aggregates
        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=instance&group_by=project&date_options=null" +
            "&resource_id=fake_resource_id%&resource_id_op=like")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = ['instance', 'instance', 'instance']
        self._verify_series(res._container[0], 4.55, '2012-12-21T11:00:55',
                            expected_names)

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_stats_with_metadata_filter(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        query = {'field': 'metadata.instance_id',
                 'value': u'instance_id'}
        # check that list is called twice for one resource and 3 tenants
        ceilometerclient.statistics.list(meter_name="instance",
                                         period=IsA(int), q=In(query)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=instance&period=60&group_by=project&date_options=null" +
            "&metadata.instance_id=instance_id")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = ['instance', 'instance', 'instance']
        self._verify_series(res._container[0], 4.55, '2012-12-21T11:00:55',
                            expected_names)

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_stats_multi_meters_with_metadata_filter(self):
        statistics = self.statistics.list()
        tenant = self.tenants.first()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False) \
            .MultipleTimes()\
            .AndReturn([[tenant], False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        query = {'field': 'metadata.instance_id',
                 'value': u'instance_id'}
        # check that list is called twice for one resource and 3 tenants
        ceilometerclient.statistics.list(meter_name="network.outgoing.bytes",
                                         period=IsA(int), q=In(query)).\
            MultipleTimes().\
            AndReturn(statistics)
        ceilometerclient.statistics.list(meter_name="network.incoming.bytes",
                                         period=IsA(int), q=In(query)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=network.outgoing.bytes-network.incoming.bytes" +
            "&group_by=project&date_options=null" +
            "&metadata.instance_id=instance_id")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = ['network.outgoing.bytes',
                          'network.incoming.bytes']
        self._verify_series(res._container[0], 4.55, '2012-12-21T11:00:55',
                            expected_names)

    def test_stats_no_groupby_with_resource_id_filter(self):
        resource = self.resources.first()
        resource_id = resource.resource_id
        statistics = self.statistics.list()

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.resources = self.mox.CreateMockAnything()
        ceilometerclient.resources.list(q=IsA(list)).AndReturn([resource])

        ceilometerclient.statistics = self.mox.CreateMockAnything()
        ceilometerclient.statistics.list(meter_name="storage.objects",
                                         period=IsA(int), q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # getting all resources and with statistics, I have only
        # 'storage.objects' defined in test data
        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=storage.objects&date_options=null" +
            "&resource_id=" + resource_id)

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = [u'storage.objects']
        self._verify_series(res._container[0], 4.55, '2012-12-21T11:00:55',
                            expected_names)

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_report(self):
        meters = self.meters.list()
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.meters = self.mox.CreateMockAnything()
        ceilometerclient.meters.list(None).AndReturn(meters)

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False). \
            MultipleTimes()\
            .AndReturn([self.tenants.list(), False])

        statistics = self.statistics.list()
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()

        ceilometerclient.statistics.list(meter_name="instance",
                                         period=IsA(int), q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)
        ceilometerclient.statistics.list(meter_name="disk.read.bytes",
                                         period=IsA(int), q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)
        ceilometerclient.statistics.list(meter_name="disk.write.bytes",
                                         period=IsA(int), q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # generate report with mock data
        res = self.client.post(reverse('horizon:admin:metering:report'),
                               data={"date_options": "7"})

        self.assertTemplateUsed(res, 'admin/metering/report.html')


class MeteringStatsTabTests(test.APITestCase):

    @test.create_stubs({api.nova: ('flavor_list',),
                        })
    def test_stats_hover_hints(self):

        class Struct(object):
            def __init__(self, d):
                self.__dict__.update(d)

        def _get_link(meter):
            link = ('http://localhost:8777/v2/meters/%s?'
                    'q.field=resource_id&q.value=ignored')
            return dict(href=link % meter, rel=meter)

        flavors = ['m1.tiny', 'm1.massive', 'm1.secret']
        resources = [
            Struct(dict(resource_id=uuid.uuid4(),
                        project_id='fake_project_id',
                        user_id='fake_user_id',
                        timestamp='2013-10-22T12:42:37',
                        metadata=dict(ramdisk_id='fake_image_id'),
                        links=[_get_link('instance:%s' % f),
                               _get_link('instance'),
                               _get_link('cpu')])) for f in flavors
        ]
        request = self.mox.CreateMock(http.HttpRequest)
        api.nova.flavor_list(request, None).AndReturn(self.flavors.list())

        ceilometerclient = self.stub_ceilometerclient()

        meters = []
        for r in resources:
            for link in r.links:
                meters.append(Struct(dict(resource_id=r.resource_id,
                                          project_id=r.project_id,
                                          user_id=r.user_id,
                                          timestamp=r.timestamp,
                                          name=link['rel'])))
        ceilometerclient.meters = self.mox.CreateMockAnything()
        ceilometerclient.meters.list(None).AndReturn(meters)

        self.mox.ReplayAll()

        tab = tabs.GlobalStatsTab(None)
        context_data = tab.get_context_data(request)

        self.assertTrue('nova_meters' in context_data)
        meter_hints = {}
        for d in context_data['nova_meters']:
            meter_hints[d.name] = d.description

        expected_meters = ['instance:%s' % f for f in flavors]
        expected_meters.extend(['instance', 'cpu'])
        for meter in expected_meters:
            self.assertTrue(meter in meter_hints)
            self.assertNotEqual(meter_hints[meter], '')


class RawSamplesViewTests(test.APITestCase, test.BaseAdminViewTests):
    URL = reverse('horizon:admin:metering:raw-samples')

    def _verify_samples(self, series, volume, timestamp, names):
        names.reverse()
        data = json.loads(series)
        self.assertTrue('series' in data)
        self.assertEqual(len(names), len(data['series']))
        for d in data['series']:
            self.assertTrue('data' in d)
            self.assertTrue(1, len(d['data']))
            self.assertAlmostEqual(volume, d['data'][0].get('y'))
            self.assertEqual(timestamp, d['data'][0].get('x'))
            self.assertEqual(names.pop(), d.get('name'))
            self.assertEqual('', d.get('unit'))

        self.assertEqual({}, data.get('settings'))

    def test_return_samples_filter_by_resource_id(self):
        samples = self.samples.list()

        # mock samples.list invoke
        client = self.stub_ceilometerclient()
        client.samples = self.mox.CreateMockAnything()
        client.samples.list(meter_name='image', q=IsA(list)).\
            AndReturn(samples)
        self.mox.ReplayAll()

        # get all samples of meter image
        #import pdb; pdb.set_trace()
        res = self.client.get(self.URL +
            "?meter=image&resource_id=fake_resource_id")
        self.assertEqual(('Content-Type', 'application/json'),
            res._headers['content-type'])
        self._verify_samples(res._container[0], 1, '2012-12-21T11:00:55',
            ['image'])

    def test_return_all_samples(self):
        samples = self.samples.list()

        # mock samples.list invoke
        client = self.stub_ceilometerclient()
        client.samples = self.mox.CreateMockAnything()
        client.samples.list(meter_name='image', q=IsA(list)).\
            AndReturn(samples)
        self.mox.ReplayAll()

        # get all samples of meter image
        res = self.client.get(self.URL +
            "?meter=image")
        self.assertEqual(('Content-Type', 'application/json'),
            res._headers['content-type'])
        self._verify_samples(res._container[0], 1, '2012-12-21T11:00:55',
            ['display_name1', u'\u4e91\u89c4\u5219'])

    def test_return_samples_with_date_options_null(self):
        samples = self.samples.list()

        # mock samples.list invoke
        client = self.stub_ceilometerclient()
        client.samples = self.mox.CreateMockAnything()

        # should query 8 hours ago samples from now
        def has_ts_filter(query):
            date_from = None
            date_to = None
            for each in query:
                if each['field'] == 'timestamp':
                    if each['op'] == 'ge':
                        date_from = each['value']
                    elif each['op'] == 'le':
                        date_to = each['value']

            if date_from is None or date_to is None:
                return False
            return (date_to - date_from).seconds == (8 * 3600)

        client.samples.list(meter_name='image', q=Func(has_ts_filter)).\
            AndReturn(samples)
        self.mox.ReplayAll()

        # get all samples of meter image
        res = self.client.get(self.URL +
            "?meter=image&resource_id=fake_resource_id")
        self.assertEqual(('Content-Type', 'application/json'),
            res._headers['content-type'])
        self._verify_samples(res._container[0], 1, '2012-12-21T11:00:55',
            ['image'])
