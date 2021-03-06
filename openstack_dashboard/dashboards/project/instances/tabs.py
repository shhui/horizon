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

from django import conf
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = ("project/instances/"
                     "_detail_overview.html")

    def get_context_data(self, request):
        instance = self.tab_group.kwargs['instance']
        instance_titles = getattr(conf.settings,
                                'INSTANCE_META_TITLES', {})
        instance_props = []

        for prop, val in instance.metadata.items():
            title = instance_titles.get(prop, prop)
            instance_props.append((prop, title, val))

        return {"instance": instance,
                "instance_props": sorted(instance_props,
                                         key=lambda prop: prop[1])}


class LogTab(tabs.Tab):
    name = _("Log")
    slug = "log"
    template_name = "project/instances/_detail_log.html"
    preload = False

    def get_context_data(self, request):
        instance = self.tab_group.kwargs['instance']
        try:
            data = api.nova.server_console_output(request,
                                                  instance.id,
                                                  tail_length=35)
        except Exception:
            data = _('Unable to get log for instance "%s".') % instance.id
            exceptions.handle(request, ignore=True)
        return {"instance": instance,
                "console_log": data}


class ConsoleTab(tabs.Tab):
    name = _("Console")
    slug = "console"
    template_name = "project/instances/_detail_console.html"
    preload = False

    def get_context_data(self, request):
        instance = self.tab_group.kwargs['instance']
        image = getattr(instance, 'image', None)
        hyper = None
        if image is not None and 'id' in image:
            image_info = api.glance.image_get(request, image['id'])
        properties = getattr(image_info, 'properties', {})
        if 'hypervisor_type' in properties:
            hyper = properties['hypervisor_type']

        meta = instance.metadata
        deploy_id = meta.get('deploy_id', "")
        powervm_mgr = meta.get('powervm_mgr', "")
        # Currently prefer VNC over SPICE, since noVNC has had much more
        # testing than spice-html5
        console_type = getattr(settings, 'CONSOLE_TYPE', 'AUTO')
        if console_type == 'AUTO':
            try:
                console = api.nova.server_vnc_console(request, instance.id)
                console_url = "%s&title=%s(%s)" % (
                    console.url,
                    getattr(instance, "name", ""),
                    instance.id)
            except Exception:
                try:
                    console = api.nova.server_spice_console(request,
                                                            instance.id)
                    console_url = "%s&title=%s(%s)" % (
                        console.url,
                        getattr(instance, "name", ""),
                        instance.id)
                except Exception:
                    try:
                        console = api.nova.server_rdp_console(request,
                                                              instance.id)
                        console_url = "%s&title=%s(%s)" % (
                            console.url,
                            getattr(instance, "name", ""),
                            instance.id)
                    except Exception:
                        console_url = None
        elif console_type == 'VNC':
            try:
                console = api.nova.server_vnc_console(request, instance.id)
                console_url = "%s&title=%s(%s)" % (
                    console.url,
                    getattr(instance, "name", ""),
                    instance.id)
            except Exception:
                console_url = None
        elif console_type == 'SPICE':
            try:
                console = api.nova.server_spice_console(request, instance.id)
                console_url = "%s&title=%s(%s)" % (
                    console.url,
                    getattr(instance, "name", ""),
                    instance.id)
            except Exception:
                console_url = None
        elif console_type == 'RDP':
            try:
                console = api.nova.server_rdp_console(request, instance.id)
                console_url = "%s&title=%s(%s)" % (
                    console.url,
                    getattr(instance, "name", ""),
                    instance.id)
            except Exception:
                console_url = None
        else:
            console_url = None

        if hyper == 'powervm':
            console_url = None
            return {'console_url': console_url, 'instance_id': instance.id,
                    'host': powervm_mgr, 'deploy_id': deploy_id}
        else:
            return {'console_url': console_url, 'instance_id': instance.id}


class CeilometerTab(tabs.Tab):
    name = _("Ceilometer")
    slug = "ceilometer"
    template_name = "project/instances/_detail_ceilometer.html"
    preload = False

    def get_context_data(self, request):
        instance = self.tab_group.kwargs['instance']
        instance_name = getattr(instance,
                                'OS-EXT-SRV-ATTR:instance_name',
                                None)
        instance_name = instance_name + "-" + instance.id
        return {'instance': instance, 'nw_resource_id': instance_name}


class ResourceUsageTab(tabs.Tab):
    name = _("Resources Usage")
    slug = "resources_usage"
    template_name = "project/instances/_detail_usage.html"
    preload = False

    @staticmethod
    def _get_flavor_names(request):
        try:
            flavors = api.nova.flavor_list(request, None)
            return [f.name for f in flavors]
        except Exception:
            return ['m1.tiny', 'm1.small', 'm1.medium',
                    'm1.large', 'm1.xlarge']

    def _get_data(self, request):
        meters = []
        meter = {'name': 'cpu', 'unit': 'ns'}
        meters.append(meter)
        meter = {'name': 'cpu_util', 'unit': '%'}
        meters.append(meter)
        meter = {'name': 'memory', 'unit': 'MB'}
        meters.append(meter)
        meter = {'name': 'memory.usage', 'unit': 'MB'}
        meters.append(meter)
        meter = {'name': 'network.outgoing.bytes', 'unit': 'B'}
        meters.append(meter)
        meter = {'name': 'network.incoming.bytes', 'unit': 'B'}
        meters.append(meter)
        meter = {'name': 'network.outgoing.packets', 'unit': 'packet'}
        meters.append(meter)
        meter = {'name': 'network.incoming.packets', 'unit': 'packet'}
        meters.append(meter)
        meter = {'name': 'disk.root.size.used', 'unit': 'GB'}
        meters.append(meter)
        meter = {'name': 'disk.root.size.used.percent', 'unit': '%'}
        meters.append(meter)
        meter = {'name': 'disk.ephemeral.size.used', 'unit': 'GB'}
        meters.append(meter)
        meter = {'name': 'disk.ephemeral.size.used.percent', 'unit': '%'}
        meters.append(meter)
        return meters

    def get_context_data(self, request):
        instance = self.tab_group.kwargs['instance']
        context = {
            'instance': instance,
        }
        return context


class InstanceDetailTabs(tabs.TabGroup):
    slug = "instance_details"
    tabs = (OverviewTab, LogTab, ConsoleTab, CeilometerTab, ResourceUsageTab)
    sticky = True
