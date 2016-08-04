import functools
import mimetypes

from tornado.auth import OAuth2Mixin, _auth_return_future, AuthError, urllib_parse
from tornado import escape


FULLCONTACT_API_URL = "https://api.fullcontact.com/v3/%s"


class FullContactMixin(OAuth2Mixin):

    """FullContact authentication using OAuth2.

    In order to use, register your application with FullContact and copy the
    relevant parameters to your application settings.
    * Go to the https://beta.fullcontact.com/apps
    * Create a new application
    * Set the Redirect URI to point to your auth handler
    * Copy the "Client ID" and "Client Secret" to the application settings as
      {"fullcontact_client_id": CLIENT_ID, "fullcontact_client_secret": CLIENT_SECRET}}
    """

    _OAUTH_AUTHORIZE_URL = "https://beta.fullcontact.com/oauth/authorize"
    _OAUTH_ACCESS_TOKEN_URL = FULLCONTACT_API_URL % "oauth.exchangeAuthCode"
    _OAUTH_NO_CALLBACKS = False

    @_auth_return_future
    def get_authenticated_user(self, redirect_uri, code, callback):
        http = self.get_auth_http_client()
        body = urllib_parse.urlencode({
            "redirect_uri": redirect_uri,
            "code": code,
            "client_id": self.settings["fullcontact_client_id"],
            "client_secret": self.settings["fullcontact_client_secret"],
        })
        http.fetch(self._OAUTH_ACCESS_TOKEN_URL,
                   functools.partial(self._on_access_token, callback),
                   method="POST", headers={'Content-Type': 'application/x-www-form-urlencoded'}, body=body)

    def _on_access_token(self, future, response):
        """Callback function for the exchange to the access token."""
        if response.error:
            future.set_exception(AuthError('FullContact auth error: %s' % str(response)))
            return
        args = escape.json_decode(response.body)
        future.set_result(args)

    @_auth_return_future
    def fullcontact_request(self, method, body=None, headers=None, callback=None, **kwargs):
        all_headers = {}
        access_token = self.current_user['access_token']
        if access_token:
            all_headers["Authorization"] = "Bearer %s" % access_token
        if headers:
            all_headers.update(headers)
        if body != None:
            body = escape.json_encode(body) if isinstance(body, dict) else body
        callback = functools.partial(self._on_oauth2_request, callback)
        http = self.get_auth_http_client()
        http.fetch(FULLCONTACT_API_URL % method, headers=all_headers, method="POST", body=body, callback=callback,
                   **kwargs)

    def fullcontact_request_multipart(self, method, body_parts, headers=None, **kwargs):
        body, content_type = encode_multipart_request(body_parts)
        headers = headers or {}
        headers["Content-Type"] = content_type
        return self.fullcontact_request(resource, body=body, headers=headers, **kwargs)


    def _on_oauth2_request(self, future, response):
        if response.error:
            future.set_exception(AuthError("Error response %s fetching %s" %
                                           (response.error, response.request.url)))
            return

        future.set_result(escape.json_decode(response.body))


# Multipart request encoding


MULTIPART_BOUNDARY = "1234cabapiclientboundary1234"


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def encode_multipart_request(body_parts):
    """Encode a multipart request payload."""

    lines = ""
    for filename, content in body_parts.items():
        lines += "--%s\n" % MULTIPART_BOUNDARY
        lines += "Content-Disposition: "
        lines += 'form-data; name="%s"; filename="%s"\r\n' % (filename, filename)
        lines += "Content-Type: %s\r\n\r\n" % get_content_type(filename)
        lines += escape.json_encode(v) if isinstance(v, dict) else v
        lines += "\r\n"
    lines += "--%s--" % MULTIPART_BOUNDARY
    return lines, "multipart/form-data; boundary=%s" % MULTIPART_BOUNDARY

