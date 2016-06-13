#!/usr/bin/env python
"""A simple FullContact CAB API demo.
To run this app, you must first register an application with FullContact:
1) Go to https://alpha.fullcontact.com/apps and create an application. Set the Redirect URI to point to your auth
   handler (or leave it empty).
2) Copy the "Client ID" and "Client Secret" to a new file config.py:
      fullcontact_client_id = '...'
      fullcontact_client_secret = '...'
3) Run this program and go to http://localhost:8080 in yourbrowser.
"""

import logging

from fullcontact.tornado.oauth2 import FullContactOAuth2Mixin, AuthError
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.options import define, options, parse_command_line, parse_config_file
from tornado.web import Application, RequestHandler, authenticated

define('port', default=8080, help="port to listen on")
define('config', default='config.py', help='filename for additional configuration')
define('debug', default=True, group='application', help="run in debug mode (with automatic reloading)")
define('fullcontact_client_id', type=str, group='application')
define('fullcontact_client_secret', type=str, group='application')
define('cookie_secret', type=str, group='application', default='REPLACT_THIS', help="signing key for secure cookies")

class BaseHandler(RequestHandler):
    COOKIE_NAME = "fullcontact_demo"

    def get_current_user(self):
        access_json = self.get_secure_cookie(self.COOKIE_NAME)
        if not access_json:
            return None
        return json_decode(access_json)

def contact_header(contact):
    d = contact["contactData"]
    photos = d.get("photos", None)
    name = d.get("name", {})
    jobs = d.get("organizations", None)
    emails = d.get("emails", None)
    return {
        "photo": photos[0].get("value", None) if photos else None,
        "name": "%s %s" % (name.get("givenName", ""), name.get("familyName", "")),
        "job": ", ".join(filter(None, [jobs[0].get(k, None) for k in ["name", "title"]])) if jobs else None,
        "email": emails[0].get("value", None) if emails else None
    }

class MainHandler(BaseHandler, FullContactOAuth2Mixin):
    @authenticated
    @gen.coroutine
    def get(self):
        try:
            res = yield self.fetch_oauth2(
                'http://cabapi.elb.fullcontact.com/v3/contacts.scroll',
                body={"abId": "4ee6f0da4dbd6c675c8f859d53b7ae0137dad808"},
                access_token=self.current_user['access_token']
            )
        except AuthError:
            self.redirect("/login")
            return
        self.render('contacts.html', contacts=map(contact_header, res["contacts"]))

class LoginHandler(BaseHandler, FullContactOAuth2Mixin):
    @gen.coroutine
    def get(self):
        redirect_uri = self.request.protocol + "://" + self.request.host + "/login"
        code = self.get_argument('code', None)
        if code:
            access = yield self.get_authenticated_user(redirect_uri=redirect_uri,
                                                       code=code)
            self.set_secure_cookie(self.COOKIE_NAME, json_encode(access))
            self.redirect('/')
        else:
            yield self.authorize_redirect(redirect_uri=redirect_uri,
                                          client_id=self.settings['fullcontact_client_id'],
                                          scope=['contacts.read'])

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie(self.COOKIE_NAME)

def main():
    parse_command_line(final=False)
    parse_config_file(options.config)
    app = Application(
        [
            ('/', MainHandler),
            ('/login', LoginHandler),
            ('/logout', LogoutHandler),
        ],
        login_url='/login',
        **options.group_dict('application'))
    app.listen(options.port)

    logging.info('Listening on http://localhost:%d' % options.port)
    IOLoop.current().start()

if __name__ == '__main__':
    main()

