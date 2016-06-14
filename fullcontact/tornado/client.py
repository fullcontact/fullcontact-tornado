import json
import urllib

from tornado import gen, httpclient

from fullcontact.tornado import HTTPClient


class CabApiClient(HTTPClient):

    @gen.coroutine
    def req(self, resource, body, token=None, headers=None, method=None):

        if token is None:
            _token = self.current_user["access_token"]
        else:
            _token = token

        _headers = {}

        if _token is not None:
            _headers["Authorization"] = "Bearer %s" % _token

        uri = "%s/v3/%s" % ("http://cabapi.elb.fullcontact.com", resource)

        if headers is not None:
            _headers.update(headers)

        _method = method if method else "POST"

        if isinstance(body, basestring):
            _body = body
        else:
            _body = json.dumps(body)

        req = httpclient.HTTPRequest(
            uri,
            method=_method,
            headers=_headers,
            body=_body
        )

        res = yield self.fetch(req)
        raise gen.Return(self.body(res))

    def req_multipart(self, resource, body_map, token=None,
                      headers=None, method=None):
        body, content_type = self._encode_multipart(body_map)

        _headers = headers
        if _headers is not None:
            _headers["Content-Type"] = content_type
        else:
            _headers = {"Content-Type": content_type}

        return self.req(
            resource,
            body,
            token=token,
            headers=_headers,
            method=method
        )

    def abs_get(self, body, token=None, headers=None):
        return self.req("abs.get", body, token=token, headers=headers)

    def account_get(self, body, token=None, headers=None):
        return self.req("account.get", body, token=token, headers=headers)

    def tags_get(self, body, token=None, headers=None):
        return self.req("tags.get", body, token=token, headers=headers)

    def tags_delete(self, body, token=None, headers=None):
        return self.req("tags.delete", body, token=token, headers=headers)

    def tags_create(self, body, token=None, headers=None):
        return self.req("tags.create", body, token=token, headers=headers)

    def tags_update(self, body, token=None, headers=None):
        return self.req("tags.update", body, token=token, headers=headers)

    def contacts_get(self, body, token=None, headers=None):
        return self.req("contacts.get", body, token=token, headers=headers)

    def contacts_create(self, body, token=None, headers=None, data=None):
        if data is not None:
            _data = {}
            _data.update(data)
            if body is not None:
                _data["contact.json"] = body
            return self.req_multipart("contacts.create", _data, token=token, headers=headers)
        else:
            return self.req("contacts.create", body, token=token, headers=headers)

    def contacts_update(self, body, token=None, headers=None, data=None, cd_name=None):
        if data is not None:
            _data = {}
            _data.update(data)
            if body is not None:
                _data[cd_name] = body
            return self.req_multipart("contacts.update", _data, token=token)
        else:
            return self.req("contacts.update", body, token=token, headers=headers)

    def contacts_delete(self, body, token=None, headers=None):
        return self.req("contacts.delete", body, token=token, headers=headers)

    def contacts_scroll(self, body, token=None, headers=None):
        return self.req("contacts.scroll", body, token=token, headers=headers)

    def contacts_search(self, body, token=None, headers=None):
        return self.req("contacts.search", body, token=token, headers=headers)

    def contacts_manage_tags(self, body, token=None, headers=None):
        return self.req("contacts.manageTags", body, token=token, headers=headers)

    def contacts_upload_photo(self, body, image_bytes, token=None, headers=None):
        return self.req_multipart(
            "contacts.uploadPhoto",
            {"contact.json": body, "image.jpg": image_bytes},
            token=token,
            headers=headers
        )
