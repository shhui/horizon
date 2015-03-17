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

from openstack_dashboard.dashboards.admin.auditlog \
    import views as admin_views
from openstack_dashboard.dashboards.project.auditlog \
    import forms as project_forms
from openstack_dashboard.dashboards.project.auditlog \
    import tables as project_tables
from openstack_dashboard.dashboards.admin.auditlog \
    import tables as admin_tables


class IndexView(admin_views.AdminIndexView):
    table_class = admin_tables.AdminAuditlogTable
    template_name = 'project/auditlog/index.html'
    form_class = project_forms.SearchForm


class DetailView(admin_views.DetailView):
    redirect_url = 'horizon:project:auditlog:index'
