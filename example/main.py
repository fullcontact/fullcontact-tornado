#!/usr/bin/env python

"""
A simple FullContact CAB API demo.

To run this app, you must first register an application with FullContact:
1) Go to https://alpha.fullcontact.com/apps and create an application.
   Set the Redirect URI to point to your auth handler (or leave it empty).
2) Copy the "Client ID" and "Client Secret" to a new file config.py:
      fullcontact_client_id = "..."
      fullcontact_client_secret = "..."
3) Run this program and go to http://localhost:8080 in yourbrowser.
"""

import logging

import fullcontact.tornado.client as client
import fullcontact.tornado.oauth2 as oauth2
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.options import define, options, parse_command_line, parse_config_file
from tornado.web import Application, RequestHandler, authenticated, URLSpec


define("port", default=8080, help="port to listen on")
define("config", default="config.py", help="filename for additional configuration")
define("debug", default=True, group="application", help="run in debug mode (with automatic reloading)")
define("fullcontact_client_id", type=str, group="application")
define("fullcontact_client_secret", type=str, group="application")
define("cookie_secret", type=str, group="application", default="REPLACE_THIS", help="signing key for secure cookies")


class BaseHandler(RequestHandler, oauth2.Oauth2Client, client.CabApiClient):

    COOKIE_NAME = "fullcontact_demo"

    def get_current_user(self):
        access_json = self.get_secure_cookie(self.COOKIE_NAME)
        if not access_json:
            return None
        return json_decode(access_json)


def format_contact(contact):

    d = contact["contactData"]
    photos = d.get("photos", None)
    name = d.get("name", {})

    emails = d.get("emails", None)

    return {
        "photo": photos[0].get("value", None) if photos else None,
        "name": name.get("givenName", ""),
        "email": emails[0].get("value", None) if emails else None
    }


def is_visible(c):
    """Returns true if contact can be displayed in the Oy app."""
    cd = c["contactData"]

    # absentPhoto is a special type that is internally known as "nophoto"
    # (ie, "contact has photos but none of them are primary")

    return cd.get("emails") and cd.get("photos") and cd["photos"][0].get("type") != "absentPhoto"


class MainHandler(BaseHandler):

    @gen.coroutine
    def fetch_contacts(self):

        # Scroll defaults to unified address book if no abId is specified.
        contacts = []

        # Fetch up to 3 pages of results.
        payload = {}
        for _ in range(3):

            res = yield self.contacts_scroll(payload)
            contacts = contacts + [c for c in res["contacts"] if is_visible(c)]

            if res.get("cursor"):
                payload["scrollCursor"] = res["cursor"]
            else:
                break
        raise gen.Return(contacts)

    @gen.coroutine
    def get(self):
        if self.current_user:
            contacts = yield self.fetch_contacts()
            anon = False
        else:
            contacts = []
            anon = True

        self.render(
            "contacts.html",
            anon=anon,
            contacts=map(format_contact, contacts)
        )


class LoginHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        req = self.request
        redirect_uri = req.protocol + "://" + req.host + self.reverse_url("login")
        code = self.get_argument("code", None)

        # Oy app has read-only contact access.
        # See cabapi documentation for read scopes
        # Each writable resource has it's own scope.

        if code:
            access = yield self.get_authenticated_user(
                redirect_uri=redirect_uri,
                code=code
            )
            self.set_secure_cookie(self.COOKIE_NAME, json_encode(access))
            self.redirect(self.reverse_url("root"))

        else:
            yield self.authorize_redirect(
                redirect_uri=redirect_uri,
                client_id=self.settings["fullcontact_client_id"],
                # for requesting read access: ["contacts.read,contacts.write"]
                scope=["contacts.read"]
            )


class LogoutHandler(BaseHandler):
    def get(self):

        self.clear_cookie(self.COOKIE_NAME)
        self.redirect(self.reverse_url("root"))


def main():

    parse_command_line(final=False)
    parse_config_file(options.config)
    handlers = [
        URLSpec("/", MainHandler, name="root"),
        URLSpec("/login", LoginHandler, name="login"),
        URLSpec("/logout", LogoutHandler, name="logout")
    ]
    app = Application(
        handlers,
        login_url="/login",
        **options.group_dict("application")
    )
    app.listen(options.port)

    logging.info("Listening on http://localhost:%d" % options.port)
    IOLoop.current().start()


if __name__ == "__main__":
    main()
