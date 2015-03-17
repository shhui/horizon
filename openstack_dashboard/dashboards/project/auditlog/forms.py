# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Kylin OS, Inc
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
from django.utils.translation import ugettext_lazy as _
import pytz

from horizon import forms
from openstack_dashboard import api
from openstack_dashboard import settings


TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
timezone = getattr(settings, 'TIME_ZONE', 'UTC')
TZ = pytz.timezone(timezone)


def get_last_hour():
    now = TZ.localize(datetime.datetime.now())
    now = now.replace(microsecond=0)
    last_hour = now - datetime.timedelta(0, 3600)
    return last_hour


class SearchForm(forms.SelfHandlingForm):
    start_date = forms.DateTimeField(label=_("Start data"),
                                   input_formats=(TIME_FORMAT),
                                   widget=forms.DateTimeInput(),
                                   required=False,
                                   initial=get_last_hour())
    end_date = forms.DateTimeField(label=_("End date"),
                             input_formats=(TIME_FORMAT),
                             widget=forms.DateTimeInput(),
                             required=False)
    path = forms.ChoiceField(label=_("Resource Type"),
                                   required=False)
    method = forms.ChoiceField(label=_("Operate Type"),
                                   required=False)

    def __init__(self, request, *args, **kwargs):
        super(SearchForm, self).__init__(request, *args, **kwargs)
        path_choices = [('', '')]
        resources = api.auditlog.resource_list(request)
        for resource in resources:
            path_choices.append((resource.rid, resource.name))
        self.fields['path'].choices = path_choices
        widget = self.fields['start_date'].widget
        widget.attrs['data-date-format'] = "yyyy-mm-dd hh:ii:ss"
        widget = self.fields['end_date'].widget
        widget.attrs['data-date-format'] = "yyyy-mm-dd hh:ii:ss"
        self.fields['method'].choices = [
            ('', ''),
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('DELETE', 'DELETE')]

    def handle(self, request, data):
        return True
