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

from csv import DictWriter  # noqa
from csv import writer  # noqa

from datetime import datetime  # noqa
from datetime import timedelta  # noqa

import json

from django.http import HttpResponse   # noqa
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView  # noqa

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon.utils import csvbase

from openstack_dashboard import api
from openstack_dashboard import usage

from openstack_dashboard.api import ceilometer
from openstack_dashboard.dashboards.admin.metering import tables as \
    metering_tables
from openstack_dashboard.dashboards.admin.metering import tabs as \
    metering_tabs


class ResourceUsageCsvRenderer(csvbase.BaseCsvResponse):

    def get_row_data(self):
        for inst in self.context['series']:
            for key, value in inst.items():
                if (key == 'data'):
                    for point in value:
                        line = []
                        i = 0
                        for k, v in point.items():
                            if (k == 'x'):
                                line.append(str(v))
                            if (k == 'y'):
                                line.append(str(v))
                            i += 1
                            if i % 2 == 0:
                                yield (line)

    def get_header_data(self):
        unit = ''
        for inst in self.context['series']:
            for key, value in inst.items():
                if (key == 'unit'):
                    unit = value
                    break
        self.columns = [_("Gauge Value") + "(" + unit + ")", _("Gauge Date")]
        self.writer = DictWriter(self.out, map(self.encode, self.columns))
        self.is_dict = True


class IndexView(tabs.TabbedTableView):
    tab_group_class = metering_tabs.CeilometerOverviewTabs
    template_name = 'admin/metering/index.html'


class SamplesView(TemplateView):
    template_name = "admin/metering/samples.csv"

    def get(self, request, *args, **kwargs):
        meter = request.GET.get('meter', None)
        if not meter:
            return HttpResponse(json.dumps({}),
                                content_type='application/json')

        date_options = request.GET.get('date_options', None)
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)
        stats_attr = request.GET.get('stats_attr', 'avg')
        group_by = request.GET.get('group_by', None)
        period = request.GET.get('period', None)
        if period is not None:
            try:
                period = int(period)
            except Exception:
                period = None
        filte_by_res = ('resource_id' in request.GET or
                        'metadata.instance_id' in request.GET)
        if filte_by_res:
            # filte by resource will return statistics of desired res,
            # so name the series to meter name
            resource_name = 'meter'
        elif group_by == "project":
            resource_name = 'id'
        else:
            resource_name = 'resource_id'

        meter_names = meter.split("-")
        if len(meter_names) > 1:
            series = []
            for meter_na in meter_names:
                resources, unit, end_date = query_data(request,
                                     date_from,
                                     date_to,
                                     date_options,
                                     group_by,
                                     meter_na,
                                     period)
                series = series + _series_for_meter(resources,
                                        resource_name,
                                        meter_na,
                                        stats_attr,
                                        unit)
        else:
            resources, unit, end_date = query_data(request,
                                         date_from,
                                         date_to,
                                         date_options,
                                         group_by,
                                         meter,
                                         period)
            series = _series_for_meter(resources,
                                            resource_name,
                                            meter,
                                            stats_attr,
                                            unit)
        ret = {}
        ret['series'] = series
        ret['settings'] = {}
        ret['last_time'] = {'date_time': end_date}

        return HttpResponse(json.dumps(ret),
            content_type='application/json')


class RawSamplesView(TemplateView):
    def get(self, request, *args, **kwargs):
        meter = request.GET.get('meter', None)
        if not meter:
            return HttpResponse(json.dumps({}),
                                content_type='application/json')

        meter_name = meter.replace(".", "_")
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)
        date_options = request.GET.get('date_options', 'null')
        resource_filter = request.GET.get('resource_id', None)
        if resource_filter:
            name_field = 'counter_name'
        else:
            name_field = 'resource_metadata.display_name'

        meter_names = meter_name.split("-")
        if len(meter_names) > 1:
            series = []
            for meter_na in meter_names:
                meter_n = meter_na.replace("_", ".")
                samples, unit, last_date = self.query_raw_sample_data(request,
                                     date_from,
                                     date_to,
                                     date_options,
                                     meter_n)
                series = series + self._series_from_samples(samples,
                                        name_field,
                                        meter_na,
                                        unit)
        else:
            samples, unit, last_date = self.query_raw_sample_data(request,
                                         date_from,
                                         date_to,
                                         date_options,
                                         meter)
            series = self._series_from_samples(samples,
                                            name_field,
                                            meter_name,
                                            unit)
        ret = {}
        ret['series'] = series
        ret['settings'] = {}
        ret['last_time'] = {'date_time': last_date}

        return HttpResponse(json.dumps(ret),
            content_type='application/json')

    def query_raw_sample_data(self, request,
                   date_from,
                   date_to,
                   date_options,
                   meter):
        interval = request.GET.get('interval_time', None)
        date_from, date_to = _calc_date_args(date_from,
                                             date_to,
                                             date_options,
                                             interval)
        queries = []
        if date_from:
            queries += [{'field': 'timestamp',
                                  'op': 'ge',
                                  'value': date_from}]
        if date_to:
            queries += [{'field': 'timestamp',
                                  'op': 'le',
                                  'value': date_to}]
        resource_id = request.GET.get('resource_id', None)
        resource_id_op = request.GET.get('resource_id_op', 'eq')
        if resource_id:
            queries += [{'field': 'resource_id',
                                  'op': resource_id_op,
                                  'value': resource_id}]
        last_search_date = date_to.strftime("%Y-%m-%d %H:%M:%S %f")
        # TODO(lsmola) replace this by logic implemented in I1 in bugs
        # 1226479 and 1226482, this is just a quick fix for RC1
        try:
            meter_list = [m for m in ceilometer.meter_list(request)
                          if m.name == meter]
            unit = meter_list[0].unit
        except Exception:
            unit = ""

        ceilometer_usage = ceilometer.CeilometerUsage(request)
        try:
            samples = ceilometer_usage.get_raw_samples(queries, meter)
        except Exception:
            samples = []
            exceptions.handle(request,
                              _('Unable to retrieve samples.'))
        return samples, unit, last_search_date

    def _series_from_samples(self, samples,
                          name_field,
                          meter_name,
                          unit):
        """Construct datapoint series for a meter from samples."""

        def _series_name_factory(field):
            def _make_name_from_metadata(sample):
                attribute = getattr(sample, attr, None)
                return attribute.get(key, '') if attribute else ''

            if field.find('.') != -1:
                attr, key = field.split('.')
                return _make_name_from_metadata
            else:
                return lambda sample: getattr(sample, field, '')

        series = {}
        name_factory = _series_name_factory(name_field)
        for sample in samples:
            name = name_factory(sample)
            date = sample.timestamp[:19]
            value = float(getattr(sample, 'counter_volume'))
            if name in series:
                series[name]['data'].append({'x': date, 'y': value})
            else:
                series[name] = {'unit': unit,
                                'name': name,
                                'data': [{'x': date, 'y': value}]}
        # sort data points by x value in asc
        for each in series.iteritems():
            each[1]['data'].sort(key=lambda p: p['x'])
        return series.values()


class ReportView(tables.MultiTableView):
    template_name = 'admin/metering/report.html'

    def get_tables(self):
        if self._tables:
            return self._tables
        project_data = self.load_data(self.request)
        table_instances = []
        limit = int(self.request.POST.get('limit', '1000'))
        for project in project_data.keys():
            table = metering_tables.UsageTable(self.request,
                                               data=project_data[project],
                                               kwargs=self.kwargs.copy())
            table.title = project
            t = (table.name, table)
            table_instances.append(t)
            if len(table_instances) == limit:
                break
        self._tables = SortedDict(table_instances)
        self.project_data = project_data
        return self._tables

    def handle_table(self, table):
        name = table.name
        handled = self._tables[name].maybe_handle()
        return handled

    def load_data(self, request):
        meters = ceilometer.Meters(request)
        services = {
            _('Nova'): meters.list_nova(),
            _('Neutron'): meters.list_neutron(),
            _('Glance'): meters.list_glance(),
            _('Cinder'): meters.list_cinder(),
            _('Swift_meters'): meters.list_swift(),
            _('Kwapi'): meters.list_kwapi(),
        }
        project_rows = {}
        date_options = request.POST.get('date_options', None)
        date_from = request.POST.get('date_from', None)
        date_to = request.POST.get('date_to', None)
        for meter in meters._cached_meters.values():
            for name, m_list in services.items():
                if meter in m_list:
                    service = name
            # show detailed samples
            # samples = ceilometer.sample_list(request, meter.name)
            res, unit, _ignore = query_data(request,
                                   date_from,
                                   date_to,
                                   date_options,
                                   "project",
                                   meter.name,
                                   3600 * 24)
            for re in res:
                values = getattr(re, meter.name)
                if values:
                    for value in values:
                        row = {"name": 'none',
                               "project": re.id,
                               "meter": meter.name,
                               "description": meter.description,
                               "service": service,
                               "time": value._apiresource.period_end,
                               "value": value._apiresource.avg}
                        if re.id not in project_rows:
                            project_rows[re.id] = [row]
                        else:
                            project_rows[re.id].append(row)
        return project_rows

    def get_context_data(self, **kwargs):
        context = {}
        context['tables'] = self.get_tables().values()
        return context


class CsvView(TemplateView):
    usage_class = usage.BaseUsage
    csv_response_class = ResourceUsageCsvRenderer
    csv_template_name = "admin/hypervisors/detail.csv"

    def get_template_names(self):
        if self.request.GET.get('format', 'html') == 'csv':
            return (self.csv_template_name or
                     ".".join((self.template_name.rsplit('.', 1)[0], 'csv')))
        return self.template_name

    def get_content_type(self):
        if self.request.GET.get('format', 'html') == 'csv':
            return "text/csv"
        return "text/html"

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('format', 'html') == 'csv':
            render_class = self.csv_response_class
            response_kwargs.setdefault("filename", "usage.csv")
        else:
            render_class = self.response_class
        resp = render_class(request=self.request,
                            template=self.get_template_names(),
                            context=context,
                            content_type=self.get_content_type(),
                            **response_kwargs)
        return resp

    def get(self, request, *args, **kwargs):
        meter = request.GET.get('meter', None)
        meter_name = meter.replace(".", "_")
        date_options = request.GET.get('date_options', None)
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)
        stats_attr = request.GET.get('stats_attr', None)
        group_by = request.GET.get('group_by', None)
        period = request.GET.get('period', None)
        resource_name = 'id' if group_by == "project" else 'resource_id'
        resource_id = request.GET.get('resource_id', None)

        meter_names = meter_name.split("-")
        if len(meter_names) > 1:
            series = []
            for meter_na in meter_names:
                meter_n = meter_na.replace("_", ".")
                resources, unit, last_date = query_data(request,
                                     date_from,
                                     date_to,
                                     date_options,
                                     group_by,
                                     meter_n,
                                     period)
                series = series + _series_for_meter(resources,
                                        resource_name,
                                        meter_na,
                                        stats_attr,
                                        unit)
        else:
            resources, unit, last_date = query_data(request,
                                         date_from,
                                         date_to,
                                         date_options,
                                         group_by,
                                         meter,
                                         period)
            series = _series_for_meter(resources,
                                            resource_name,
                                            meter,
                                            stats_attr,
                                            unit)

        self.kwargs['series'] = series

        self.kwargs['resource_id'] = resource_id
        self.kwargs['meter'] = meter
        self.kwargs['date_options'] = date_options
        self.kwargs['date_from'] = date_from
        self.kwargs['date_to'] = date_to
        self.kwargs['stats_attr'] = stats_attr
        self.kwargs['period'] = period

        return self.render_to_response(self.get_context_data(**kwargs))

    def get_context_data(self, **kwargs):
        context = super(CsvView, self).get_context_data(**kwargs)
        context['series'] = self.kwargs['series']

        context['resource_id'] = self.kwargs['resource_id']
        context['meter'] = self.kwargs['meter']
        context['date_options'] = self.kwargs['date_options']
        context['date_from'] = self.kwargs['date_from']
        context['date_to'] = self.kwargs['date_to']
        context['stats_attr'] = self.kwargs['stats_attr']
        context['period'] = self.kwargs['period']
        return context


def _series_for_meter(aggregates,
                      resource_name,
                      meter_name,
                      stats_name,
                      unit):
    """Construct datapoint series for a meter from resource aggregates."""
    series = []
    for resource in aggregates:
        if getattr(resource, meter_name):
            if resource_name == 'meter':
                name = meter_name
            else:
                name = getattr(resource, resource_name)

            point = {'unit': unit,
                     'name': name,
                     'data': []}
            for statistic in getattr(resource, meter_name):
                date = statistic.duration_end[:19]
                value = float(getattr(statistic, stats_name))
                point['data'].append({'x': date, 'y': value})
            series.append(point)
    return series


def _calc_period(date_from, date_to):
    if date_from and date_to:
        if date_to < date_from:
            # TODO(lsmola) propagate the Value error through Horizon
            # handler to the client with verbose message.
            raise ValueError("Date to must be bigger than date "
                             "from.")
            # get the time delta in seconds
        delta = date_to - date_from
        if delta.days <= 0:
            # it's one day
            delta_in_seconds = 3600 * 24
        else:
            delta_in_seconds = delta.days * 24 * 3600 + delta.seconds
            # Lets always show 400 samples in the chart. Know that it is
        # maximum amount of samples and it can be lower.
        number_of_samples = 400
        period = delta_in_seconds / number_of_samples
    else:
        # If some date is missing, just set static window to one day.
        period = 3600 * 24
    return period


def _calc_date_args(date_from, date_to, date_options, interval_time):
    # TODO(lsmola) all timestamps should probably work with
    # current timezone. And also show the current timezone in chart.
    if (date_options == "other"):
        try:
            if date_from:
                date_from = datetime.strptime(date_from,
                                              "%Y-%m-%d")
            else:
                # TODO(lsmola) there should be probably the date
                # of the first sample as default, so it correctly
                # counts the time window. Though I need ordering
                # and limit of samples to obtain that.
                pass
            if date_to:
                date_to = datetime.strptime(date_to,
                                            "%Y-%m-%d")
                # It return beginning of the day, I want the and of
                # the day, so i will add one day without a second.
                date_to = (date_to + timedelta(days=1) -
                           timedelta(seconds=1))
            else:
                date_to = datetime.now()
        except Exception:
            raise ValueError("The dates haven't been "
                             "recognized")
    elif(date_options == "null"):
        if interval_time:
#             date_from = datetime.utcnow() - \
#                 timedelta(seconds=int(60))
            date_from = datetime.strptime(interval_time,
               "%Y-%m-%d %H:%M:%S %f")

            date_to = datetime.utcnow()
        else:
            date_from = datetime.utcnow() - timedelta(hours=8)
            date_to = datetime.utcnow()
    else:
        try:
            date_from = datetime.now() - timedelta(days=int(date_options))
            date_to = datetime.now()
        except Exception:
            raise ValueError("The time delta must be an "
                             "integer representing days.")
    return date_from, date_to


def query_data(request,
               date_from,
               date_to,
               date_options,
               group_by,
               meter,
               period=None):
    interval_time = request.GET.get('interval_time', None)
    date_from, date_to = _calc_date_args(date_from,
                                         date_to,
                                         date_options,
                                         interval_time)
    if not period:
        period = _calc_period(date_from, date_to)
    additional_query = []
    if date_from:
        additional_query += [{'field': 'timestamp',
                              'op': 'ge',
                              'value': date_from}]
    if date_to:
        additional_query += [{'field': 'timestamp',
                              'op': 'le',
                              'value': date_to}]
    last_search_date = date_to.strftime("%Y-%m-%d %H:%M:%S %f")
    resource_id = request.GET.get('resource_id', None)
    resource_id_op = request.GET.get('resource_id_op', 'eq')

    # NOTE(xg.song): if query samples of a resource, filter the
    # resources by it's resource_id or metadata.instance_id for
    # resources which's id is not resource_id (such as NIC samples)
    filted = False
    if resource_id:
        if meter == 'network.outgoing.bytes.rate' or \
                meter == 'network.incoming.bytes.rate' or \
                meter == 'network.outgoing.packets.rate' or \
                meter == 'network.incoming.packets.rate':
            additional_query += [{'field': 'metadata.instance_id',
                                  'op': resource_id_op,
                                  'value': resource_id}]
        else:
            additional_query += [{'field': 'resource_id',
                                  'op': resource_id_op,
                                  'value': resource_id}]
        filted = True

    metadata = request.GET.get('metadata.instance_id', None)
    if metadata:
        additional_query += [{'field': 'metadata.instance_id',
                              'value': metadata}]
        filted = True

    # TODO(lsmola) replace this by logic implemented in I1 in bugs
    # 1226479 and 1226482, this is just a quick fix for RC1

    try:
        meter_list = [m for m in ceilometer.meter_list(request)
                      if m.name == meter]
        unit = meter_list[0].unit
    except Exception:
        unit = ""
    if group_by == "project":
        try:
            tenants, more = api.keystone.tenant_list(
                request,
                domain=None,
                paginate=False)
        except Exception:
            tenants = []
            exceptions.handle(request,
                              _('Unable to retrieve tenant list.'))
        queries = {}
        for tenant in tenants:
            tenant_query = [{
                "field": "project_id",
                "op": "eq",
                "value": tenant.id}]
            queries[tenant.name] = tenant_query

        ceilometer_usage = ceilometer.CeilometerUsage(request)
        resources = ceilometer_usage.resource_aggregates_with_statistics(
            queries, [meter], period=period, stats_attr=None,
            additional_query=additional_query)

    else:
        query = []

        if filted:
            query = additional_query

        def filter_by_meter_name(resource):
            """Function for filtering of the list of resources.

            Will pick the right resources according to currently selected
            meter.
            """
            for link in resource.links:
                if link['rel'] == meter:
                    # If resource has the currently chosen meter.
                    return True
            return False

        ceilometer_usage = ceilometer.CeilometerUsage(request)
        try:
            resources = ceilometer_usage.resources_with_statistics(
                query, [meter], period=period, stats_attr=None,
                additional_query=additional_query,
                filter_func=filter_by_meter_name)
        except Exception:
            resources = []
            exceptions.handle(request,
                              _('Unable to retrieve statistics.'))
    return resources, unit, last_search_date
