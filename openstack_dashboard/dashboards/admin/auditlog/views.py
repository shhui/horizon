# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 OpenStack Foundation
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

import datetime
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
import pytz


from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.auditlog \
    import forms as admin_forms
from openstack_dashboard.dashboards.admin.auditlog \
    import tables as admin_tables
from openstack_dashboard.dashboards.admin.auditlog \
    import tabs as admin_tabs
from openstack_dashboard.dashboards.project.auditlog \
    import tables as project_tables
from openstack_dashboard.openstack.common import timeutils
from openstack_dashboard import settings


ISO_TIME_FORMAT = timeutils._ISO8601_TIME_FORMAT
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
timezone = getattr(settings, 'TIME_ZONE', 'UTC')
TZ = pytz.timezone(timezone)


class AdminIndexView(tables.DataTableView, forms.ModalFormView):
    table_class = admin_tables.AdminAuditlogTable
    form_class = admin_forms.SearchForm
    template_name = 'admin/auditlog/index.html'
    success_url = reverse_lazy("horizon:admin:auditlog:index")

    def get_context_data(self, **kwargs):
        context = super(AdminIndexView, self).get_context_data(
            **kwargs)
        context['form'] = self.get_form(self.form_class)
        return context

    def has_more_data(self, table):
        return self._more

    def get_data(self, **kwargs):
        auditlogs = []
        marker = self.request.GET.get(
            admin_tables.AdminAuditlogTable._meta.pagination_param, None)

        last_hour = get_last_hour()
        if marker:
            user_id = self.request.GET.get('user_id')
            tenant_id = self.request.GET.get('tenant_id')
            start_date = self.request.GET.get('start_date')
            #(NOTE st.wang) change time format
            if start_date:
                start = timeutils.parse_strtime(start_date, ISO_TIME_FORMAT)
                start_date = timeutils.strtime(start, TIME_FORMAT)
            end_date = self.request.GET.get('end_date')
            if end_date:
                end = timeutils.parse_strtime(end_date, ISO_TIME_FORMAT)
                end_date = timeutils.strtime(end, TIME_FORMAT)
            path = self.request.GET.get('path')
            method = self.request.GET.get('method')
        else:
            user_id = self.request.POST.get('user_id')
            tenant_id = self.request.POST.get('tenant_id')
            start_date = self.request.POST.get('start_date', last_hour)
            end_date = self.request.POST.get('end_date')
            path = self.request.POST.get('path')
            method = self.request.POST.get('method')

        q = query_data(self.request,
                           user_id,
                           tenant_id,
                           start_date,
                           end_date,
                           path,
                           method,
                           marker)

        admin_tables.AdminAuditlogTable._meta.data_fields = q
        project_tables.AuditlogTable._meta.data_fields = q
        try:
            auditlogs, self._more = api.auditlog.auditlog_list(
                self.request,
                marker=marker,
                paginate=True,
                q=q)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _('Unable to retrieve auditlogs list.'))
        if auditlogs:
            try:
                tenants, has_more = api.keystone.tenant_list(self.request)
            except Exception:
                tenants = []
                msg = _('Unable to retrieve auditlogs information.')
                exceptions.handle(self.request, msg)

            try:
                users = api.keystone.user_list(self.request)
            except Exception:
                users = []
                msg = _('Unable to retrieve auditlogs user information.')
                exceptions.handle(self.request, msg)
            try:
                resources = api.auditlog.resource_list(self.request)
            except Exception:
                resources = []
                msg = _('Unable to retrieve auditlogs resource information.')
                exceptions.handle(self.request, msg)
            tenant_dict = SortedDict([(f.id, f) for f in tenants])
            user_dict = SortedDict([(t.id, t) for t in users])
            resource_dict = SortedDict([(r.rid, r) for r in resources])
            tz_utc = pytz.timezone('UTC')
            for auditlog in auditlogs:
                auditlog.display_id = "(" + auditlog.id.split('-')[0] + ")"
                tenant = tenant_dict.get(auditlog.tenant_id, None)
                user = user_dict.get(auditlog.user_id, None)
                resource = resource_dict.get(auditlog.rid, None)
                auditlog.tenant_name = getattr(tenant, "name", None)
                auditlog.user_name = getattr(user, "name", None)
                auditlog.path = getattr(resource, "name", None)
                auditlog.status_code = get_status_code(auditlog.status_code)
                # NOTE(xg.song) defence code to ignore microsecond
                str_begin = auditlog.begin_at.split('.')[0]
                begin_utc = timeutils.parse_strtime(str_begin,
                                                    ISO_TIME_FORMAT)
                begin_utc = begin_utc.replace(tzinfo=tz_utc)
                begin_local = TZ.fromutc(begin_utc)
                begin = timeutils.strtime(begin_local, TIME_FORMAT)
                # NOTE(xg.song) defence code to ignore microsecond
                str_end = auditlog.end_at.split('.')[0]
                end_utc = timeutils.parse_strtime(str_end,
                                                    ISO_TIME_FORMAT)
                end_utc = end_utc.replace(tzinfo=tz_utc)
                end_local = TZ.fromutc(end_utc)
                end = timeutils.strtime(end_local, TIME_FORMAT)
                auditlog.begin_at = begin
                auditlog.end_at = end
        return auditlogs

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        if form.is_valid():
            kwargs['form'] = form
            return self.get(request, *args, **kwargs)
        else:
            kwargs['form'] = form
            return self.get(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Returns the keyword arguments for instantiating the form."""
        kwargs = {'initial': self.get_initial()}

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        elif self.request.method in ('GET'):
            #(NOTE st.wang)initial auditlog button is GET method
            #if 'GET' is empty use initial start_date
            #else change the time format
            if self.request.GET:
                request = self.request.GET.copy()
                start_date = request['start_date']
                start = timeutils.parse_strtime(start_date, ISO_TIME_FORMAT)
                start_date = timeutils.strtime(start, TIME_FORMAT)
                request.update({'start_date': start_date})
                if request.get('end_date', None):
                    end_date = request['end_date']
                    end = timeutils.parse_strtime(end_date, ISO_TIME_FORMAT)
                    end_date = timeutils.strtime(end, TIME_FORMAT)
                    request.update({'end_date': end_date})
                kwargs.update({
                    'data': request,
                    'files': self.request.FILES,
                })
        return kwargs


def get_status_code(code):
        if code < 200:
            return "Informational"
        elif (code >= 200 and code < 300):
            return "Success"
        elif (code >= 300 and code < 400):
            return "Redirection"
        elif (code >= 400 and code < 500):
            return "Client Error"
        else:
            return "Server Error"


def query_data(request,
               user_id,
               tenant_id,
               start_date,
               end_date,
               path,
               method,
               marker):
    query = []
    if start_date:
        start = timeutils.parse_strtime(start_date, TIME_FORMAT)
        start_local = TZ.localize(start)
        utc = timeutils.normalize_time(start_local)
        start_date = timeutils.strtime(utc, ISO_TIME_FORMAT)
        start_date = unicode(start_date, "utf-8")
        query += [{"field": "begin_at",
                   "op": "ge",
                   "type": "string",
                   "value": start_date}]
    if end_date:
        end = datetime.datetime.strptime(end_date, TIME_FORMAT)
        end_local = TZ.localize(end)
        utc = timeutils.normalize_time(end_local)
        end_date = timeutils.strtime(utc, ISO_TIME_FORMAT)
        end_date = unicode(end_date, "utf-8")
        query += [{"field": "begin_at",
                   "op": "le",
                   "type": "string",
                   "value": end_date}]
    if user_id:
        query += [{"field": "user_id",
                   "op": "eq",
                   "type": "string",
                   "value": user_id}]
    if tenant_id:
        query += [{"field": "tenant_id",
                   "op": "eq",
                   "type": "string",
                   "value": tenant_id}]
    if path:
        query += [{"field": "rid",
                   "op": "eq",
                   "type": "string",
                   "value": path}]
    if method:
        query += [{"field": "method",
                   "op": "eq",
                   "type": "string",
                   "value": method}]
    return query


def get_last_hour():
    now = TZ.localize(datetime.datetime.now())
    now = now.replace(microsecond=0)
    last_hour = now - datetime.timedelta(0, 3600)
    return timeutils.strtime(last_hour, TIME_FORMAT)


class DetailView(tabs.TabView):
    tab_group_class = admin_tabs.AuditlogDetailTabs
    template_name = 'admin/auditlog/detail.html'
    redirect_url = 'horizon:admin:auditlog:index'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["auditlogs"] = self.get_data()
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            auditlog = api.auditlog.auditlog_get(self.request,
                              self.kwargs['auditlog'])
        except Exception:
            redirect = reverse(self.redirect_url)
            exceptions.handle(self.request,
                              _('Unable to retrieve details'),
                                redirect=redirect)
            raise exceptions.Http302(redirect)
        return auditlog

    def get_tabs(self, request, *args, **kwargs):
        auditlog = self.get_data()
        return self.tab_group_class(request, auditlogs=auditlog, **kwargs)
