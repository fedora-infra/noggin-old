import requests


def discover(baseurl, version=None):
    if version is None:
        versions = discover_api_versions(baseurl)
        version = versions["default_version"]
    else:
        if isinstance(version, int):
            version = 'v%s' % version
    return discover_api_version_documentation(baseurl, version)


def discover_api_version_documentation(baseurl, apiver):
    resp = requests.get("%s/doc/%s.json" % (baseurl, apiver))
    resp.raise_for_status()
    return resp.json()


def discover_api_versions(baseurl):
    resp = requests.get(baseurl)
    resp.raise_for_status()
    return resp.json()
