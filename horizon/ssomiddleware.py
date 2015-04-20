# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
"""
Middleware provided and used by Horizon.
"""

import ldap
import logging
import time

from django.conf import settings
from django.contrib import auth  # noqa
from django import http
from django.utils import timezone
from openstack_auth import forms
from openstack_auth import user as auth_user

LOG = logging.getLogger(__name__)

LDAP_HOST = "ldap://192.168.0.214:389"
BASE_DN = "ou=Users,dc=venus,dc=com"
LDAP_USER = "cn=Manager,dc=venus,dc=com"
LDAP_PASS = "123456"


def get_passwd(username):
    try:
        l = ldap.initialize(LDAP_HOST)
        l.protocol_version = ldap.VERSION3
        l.simple_bind(LDAP_USER, LDAP_PASS)

        searchScope = ldap.SCOPE_SUBTREE
#        searchFiltername = "sAMAccountName"
        searchFilter = 'sn=%s' % username
        resultID = l.search(BASE_DN, searchScope, searchFilter, None)

        result_type, result_data = l.result(resultID, 0)
        if(not len(result_data) == 0):
            r_a, r_b = result_data[0]
            return r_b['userPassword'][0]
        else:
            return None
    except ldap.LDAPError:
        return None


class HorizonTokenMiddleware(object):
    """The middleware class. Required for SSO."""

    def process_request(self, request):
        # Activate timezone handling
        tz = request.session.get('django_timezone')
        if tz:
            timezone.activate(tz)

        # Check for session timeout
        try:
            timeout = settings.SESSION_TIMEOUT
        except AttributeError:
            timeout = 1800

        username = request.META.get('HTTP_IV_USER', None)
        if username:
            last_activity = request.session.get('last_activity', None)
            timestamp = int(time.time())
            istimeout = (isinstance(last_activity, int)
                and (timestamp - last_activity) > timeout)
            noauth = (not hasattr(request, "user")
                or not request.user.is_authenticated())
            if istimeout or noauth:
                password = get_passwd(username)
                default_domain = getattr(settings,
                                         'OPENSTACK_KEYSTONE_DEFAULT_DOMAIN',
                                         'Default')
                self.user_cache = auth.authenticate(
                    request=request,
                    username=username,
                    password=password,
                    user_domain_name=default_domain)
                auth.login(request, self.user_cache)
                if request.user.is_authenticated():
                    auth_user.set_session_from_user(request, request.user)
                    regions = dict(forms.Login.get_region_choices())
                    region = request.user.endpoint
                    region_name = regions.get(region)
                    request.session['region_endpoint'] = region
                    request.session['region_name'] = region_name
                    request.session['last_activity'] = int(time.time())
        else:
            response = http.HttpResponse(status=401)
            return response
