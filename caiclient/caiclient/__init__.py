import requests
from openidc_client import OpenIDCClient

from caiclient.discovery import discover


class CAIClient(object):
    def __init__(self, baseurl, oidc_client_info, api_version=None):
        self.baseurl = baseurl
        self.api_definition = discover(baseurl, api_version)
        self.oidc_client = OpenIDCClient(**oidc_client_info)

    def get_user_token(self, required_scopes):
        pass

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
        # TODO: User and client auth
        if operinfo["auth"]["user"] is not False:
            usertoken = self.get_user_token(operinfo["auth"]["user"])
            if not usertoken:
                raise RuntimeError("No user token present")
            kwargs["headers"]["Authorization"] = "Bearer %s" % usertoken
        resp = requests.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()
