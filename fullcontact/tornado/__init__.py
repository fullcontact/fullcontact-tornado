import json

from tornado import httpclient


class HTTPClient(object):

    _MULTIPART_BOUNDARY = "1234cabapiclientboundary1234"

    def _encode_multipart(self, parts):
        """Encode a multipart request payload."""

        lines = ""
        for k, v in parts.items():

            lines += "--%s\n" % self._MULTIPART_BOUNDARY
            lines += "Content-Disposition: "
            lines += 'form-data; name="%s"; filename="%s"\r\n' % (k, k)
            if isinstance(v, dict):
                lines += "Content-Type: application/json\r\n\r\n"
                lines += '%s\r\n' % (json.dumps(v))
            else:
                lines += "Content-Type: image/jpeg\r\n\r\n"
                lines += v
                lines += "\r\n"
        lines += "--%s--" % self._MULTIPART_BOUNDARY
        return lines, "multipart/form-data; boundary=%s" % self._MULTIPART_BOUNDARY

    def fetch(self, request):
        client = httpclient.AsyncHTTPClient()
        return client.fetch(request)

    def get(self, url):
        return self.fetch(httpclient.HTTPRequest(url))

    def post(self, url, body):
        return self.fetch(httpclient.HTTPRequest(url, method="POST", body=json.dumps(body)))

    def body(self, res):
        """
            Returns decoded response body.
        """

        if hasattr(res, "body"):
            return json.loads(res.body)
        else:
            return json.loads(res.response.body)
