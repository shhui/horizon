# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

import ldap
import time

from django.conf import settings
from django.contrib import auth  # noqa

from horizon import ssomiddleware
from horizon.test import helpers as test

from mox import IgnoreArg  # noqa
from mox import IsA  # noqa
from openstack_auth import forms
from openstack_auth import user as auth_user


class TokenMiddlewareTests(test.TestCase):

    def test_process_process_no_username(self):
        requested_url = '/project/'
        request = self.factory.get(requested_url)
        mw = ssomiddleware.HorizonTokenMiddleware()
        resp = mw.process_request(request)
        self.assertEqual(resp.status_code, 401)

    def test_process_process_notimeout_and_authed(self):
        requested_url = '/project/'
        username = 'username'
        request = self.factory.get(requested_url)
        request.session['last_activity'] = int(time.time())
        request.META['HTTP_IV_USER'] = username
        mw = ssomiddleware.HorizonTokenMiddleware()
        resp = mw.process_request(request)
        self.assertIsNone(resp)

    def test_process_process(self):
        mw = ssomiddleware.HorizonTokenMiddleware()
        requested_url = '/project/'
        request = self.factory.get(requested_url)
        username = 'username'
        password = 'password'
        regions = ['r1', ]

        try:
            timeout = settings.SESSION_TIMEOUT
        except AttributeError:
            timeout = 1800

        request.session = self.client._session()
        request.session['last_activity'] = int(time.time()) - (timeout + 10)
        request.user.endpoint = 'r'
        request.META['HTTP_IV_USER'] = username

        self.mox.StubOutWithMock(ssomiddleware, "get_passwd")
        self.mox.StubOutWithMock(auth, "authenticate")
        self.mox.StubOutWithMock(auth, "login")
        self.mox.StubOutWithMock(auth_user, "set_session_from_user")
        self.mox.StubOutWithMock(forms.Login, "get_region_choices")

        ssomiddleware.get_passwd(username).AndReturn(password)
        auth.authenticate(request=request, username=username,
                          password=password, user_domain_name='Default')
        auth.login(request, None).AndReturn(None)
        auth_user.set_session_from_user(request,
                                        request.user).AndReturn(request)
        forms.Login.get_region_choices().AndReturn(regions)

        self.mox.ReplayAll()
        resp = mw.process_request(request)
        self.assertIsNone(resp)
