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

from django.utils.translation import ugettext_lazy as _

import horizon


class SystemPanels(horizon.PanelGroup):
    slug = "admin"
    name = _("System Panel")
    panels = ('overview', 'metering', 'info')


class IdentityPanels(horizon.PanelGroup):
    slug = "identity"
    name = _("Identity Panel")
    panels = ('domains', 'projects', 'users', 'groups', 'roles')


class ComputePanels(horizon.PanelGroup):
    slug = "compute"
    name = _("Compute")
    panels = ('hypervisors', 'aggregates', 'instances', 'flavors', 'images')


class StoragePanels(horizon.PanelGroup):
    slug = "storage"
    name = _("Storage")
    panels = ('volumes',)


class NetworkPanels(horizon.PanelGroup):
    slug = "network"
    name = _("Network Panel")
    panels = ('networks', 'routers')


class AuditlogPanels(horizon.PanelGroup):
    slug = "auditlog"
    name = _("Auditlog")
    panels = ('auditlog',)


class Admin(horizon.Dashboard):
    name = _("Admin")
    slug = "admin"
    panels = (SystemPanels, ComputePanels, StoragePanels,
              NetworkPanels, IdentityPanels, AuditlogPanels)
    default_panel = 'overview'
    permissions = ('openstack.roles.admin',)

    def nav(self, context):
        dash = context['request'].horizon.get('dashboard', None)
        if dash and dash.slug == self.slug:
            return True
        return False


horizon.register(Admin)
