# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.template.defaultfilters import title  # noqa
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import tables


class AdminAuditlogTable(tables.DataTable):
    display_id = tables.Column("display_id",
                               link=("horizon:admin:auditlog:detail"),
                               verbose_name=_("Id"))
    user = tables.Column("user_name", verbose_name=_("User"))
    tenant = tables.Column("tenant_name", verbose_name=_("Tenant"))
    path = tables.Column("path", verbose_name=_("Resource"))
    method = tables.Column("method",
                           verbose_name=_("Operate type"))
    status = tables.Column("status_code",
                           verbose_name=_("Result"))
    begin_at = tables.Column("begin_at",
                             verbose_name=_("Operate start time"),
                             attrs={'data-type': 'parse_isotime'})
    end_at = tables.Column("end_at",
                           verbose_name=_("Operate end time"),
                           attrs={'data-type': 'parse_isotime'})

    class Meta:
        name = "auditlog"
        verbose_name = _("Auditlog")

    def get_pagination_string(self):
        pageurl = "=".join([self._meta.pagination_param, self.get_marker()])
        for field in self._meta.data_fields:
            if field['field'] == "rid":
                params = urlencode({"path": field['value']})
                pageurl = "&".join([pageurl, params])
            elif field['field'] == "begin_at":
                if field['op'] == "ge":
                    params = urlencode({"start_date": field['value']})
                    pageurl = "&".join([pageurl, params])
                elif field['op'] == "le":
                    params = urlencode({"end_date": field['value']})
                    pageurl = "&".join([pageurl, params])
            else:
                params = urlencode({field['field']: field['value']})
                pageurl = "&".join([pageurl, params])
        """Returns the query parameter string to paginate this table."""
        return pageurl
