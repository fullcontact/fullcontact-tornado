import functools

from tornado.auth import OAuth2Mixin, _auth_return_future, AuthError, urllib_parse
from tornado import escape


class Oauth2Client(OAuth2Mixin):

    """FullContact authentication using OAuth2.

    In order to use, register your application with FullContact and copy the
    relevant parameters to your application settings.
    * Go to the https://alpha.fullcontact.com/apps
    * Create a new application
    * Set the Redirect URI to point to your auth handler
    * Copy the "Client ID" and "Client Secret" to the application settings as
      {"fullcontact_client_id": CLIENT_ID, "fullcontact_client_secret": CLIENT_SECRET}}
    """

    _OAUTH_AUTHORIZE_URL = "https://alpha.fullcontact.com/oauth/authorize"
    _OAUTH_ACCESS_TOKEN_URL = "https://api.fullcontact.com/v3/oauth.exchangeAuthCode"
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

    def _on_oauth2_request(self, future, response):
        if response.error:
            future.set_exception(AuthError("Error response %s fetching %s" %
                                           (response.error, response.request.url)))
            return

        future.set_result(escape.json_decode(response.body))
