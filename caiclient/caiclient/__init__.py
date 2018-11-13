import requests
from openidc_client import OpenIDCClient

from caiclient.discovery import discover


class CAIClient(object):
    def __init__(self, baseurl, oidc_client_info, api_version=None):
        self.baseurl = baseurl
        self.api_definition = discover(baseurl, api_version)
        self.oidc_client = OpenIDCClient(**oidc_client_info)

    def get_user_token(self, required_scopes):
        return self.oidc_client.get_token(required_scopes)

    def __call__(self, operation, method, args, check_validity=True):
        operinfo = self.api_definition["operations"][operation][method]
        for arg in operinfo["arguments"]:
            if arg["required"] and arg["name"] not in args:
                raise ValueError("%s to %s requires %s" %
                                 (method, operation, arg["name"]))

        url = "%s/%s/%s" % (self.baseurl,
                            self.api_definition["version"],
                            operation)
        method = method.upper()
        kwargs = {"headers": {}}
        if method not in ("GET", "HEAD"):
            kwargs["json"] = args

        if operinfo["auth"]["user"] is not False:
            usertoken = self.get_user_token(operinfo["auth"]["user"])
            if not usertoken:
                raise RuntimeError("No user token present")
            kwargs["headers"]["Authorization"] = "Bearer %s" % usertoken
        # TODO: Client auth
        resp = requests.request(method, url, **kwargs)
        if resp.status_code == 401:
            # OpenIDC-Client is responsible for erroring if we call twice
            new_token = self.oidc_client.report_token_issue()
            if not new_token:
                resp.raise_for_status()
            return self(operation, method, args, check_validity=False)
        resp.raise_for_status()
        return resp.json()
