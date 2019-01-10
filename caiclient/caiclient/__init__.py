from base64 import b64encode
from binascii import a2b_hex
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
import json
import requests
from openidc_client import OpenIDCClient

from caiclient.discovery import discover


class CAIClient(object):
    def __init__(self, baseurl, client_info, oidc_client_info,
                 api_version=None):
        self.baseurl = baseurl
        self.api_definition = discover(baseurl, api_version)
        self.client_info = client_info
        self.oidc_client = OpenIDCClient(**oidc_client_info)

    def get_user_token(self, required_scopes):
        return self.oidc_client.get_token(required_scopes)

    def sign_request(self, url, method, token, req):
        secret = self.client_info['secret']
        if isinstance(secret, str):
            secret = a2b_hex(secret)
        h = hmac.HMAC(secret,
                      hashes.SHA256(),
                      backend=default_backend())
        h.update(url.encode('utf-8'))
        h.update(b'_')
        h.update(method.lower().encode('utf-8'))
        h.update(b'_')
        if token:
            h.update(token.encode('utf-8'))
        else:
            h.update(b'NOUSER')
        h.update(b'_')
        h.update(req.encode('utf-8'))
        sig = b64encode(h.finalize())
        return 'sha256:%s' % sig.decode('utf-8')

    def __call__(self, operation, method, args, check_validity=True,
                 is_retry=False):
        operinfo = self.api_definition["operations"][operation][method]
        for arg in operinfo["arguments"]:
            if arg["required"] and arg["name"] not in args:
                raise ValueError("%s to %s requires %s" %
                                 (method, operation, arg["name"]))

        relurl = "/%s/%s" % (self.api_definition["version"],
                             operation)
        url = "%s%s" % (self.baseurl, relurl)
        method = method.upper()
        kwargs = {"headers": {}}
        if method not in ("GET", "HEAD"):
            kwargs["data"] = json.dumps(args)
            kwargs["headers"]["Content-Type"] = "application/json"

        usertoken = None
        if operinfo["auth"]["user"] is not False:
            usertoken = self.get_user_token(operinfo["auth"]["user"])
            if not usertoken:
                raise RuntimeError("No user token present")
            kwargs["headers"]["Authorization"] = "Bearer %s" % usertoken
        # Add Client Authentication signature
        kwargs["headers"]["X-CAIAPI-Client-Name"] = self.client_info["name"]
        kwargs["headers"]["X-CAIAPI-Client-Sig"] = self.sign_request(
            relurl, method, usertoken, kwargs.get("data"),
        )
        # Perform request
        resp = requests.request(method, url, **kwargs)
        rcodes = [int(code) for code in operinfo['return_codes'].keys()]
        if resp.status_code == 401:
            authhdr = resp.headers.get("WWW-Authenticate")
            if authhdr == 'CAIAPI-Client':
                raise Exception("Client authentication failed")
            elif authhdr != 'Bearer':
                raise Exception("Unknown authentication error: %s" % authhdr)
            if is_retry:
                raise Exception("Authentication error")
            new_token = self.oidc_client.report_token_issue()
            if not new_token:
                resp.raise_for_status()
            return self(operation, method, args, check_validity=False,
                        is_retry=True)
        elif resp.status_code == 500:
            # TODO: Fix exception type
            raise Exception("Error calling API: %s" % resp.json())
        elif resp.status_code not in rcodes:
            # TODO: Fix exception type
            raise ValueError("API returned an unexpected return code: %d!")
        return resp.json()
