

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

from __future__ import absolute_import

import itertools
import logging

from django.conf import settings

import auditlogclient.client as auditlog_client

from horizon.utils import functions as utils

from openstack_dashboard.api import base


LOG = logging.getLogger(__name__)


def auditlogclient(request):
    endpoint = base.url_for(request, 'auditlog')
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    LOG.debug('auditlogclient connection created using token "%s" '
              'and endpoint "%s"' % (request.user.token.id, endpoint))
    return auditlog_client.Client('1', endpoint,
                                    token=(lambda: request.user.token.id),
                                    insecure=insecure,
                                    ca_file=cacert)


def auditlog_get(request, auditlog_id):
    """Returns an auditlog object populated with metadata for auditlog
    with supplied identifier.
    """
    auditlog = auditlogclient(request).auditlog.get(auditlog_id)
    return auditlog


def auditlog_list(request, marker=None, q=None, paginate=False):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    page_size = utils.get_page_size(request)
    c = auditlogclient(request)

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

    kwargs = {'q': q or {}}
    if marker:
        kwargs['marker'] = marker

    auditlogs_iter = c.auditlog.list(page_size=request_size,
                                    limit=limit,
                                    **kwargs)
    has_more_data = False
    if paginate:
        auditlogs = list(itertools.islice(auditlogs_iter, request_size))
        if len(auditlogs) > page_size:
            auditlogs.pop(-1)
            has_more_data = True
    else:
        auditlogs = list(auditlogs_iter)
    return (auditlogs, has_more_data)


def resource_list(request):
    resources = auditlogclient(request).auditlog.list_resource()
    return resources
