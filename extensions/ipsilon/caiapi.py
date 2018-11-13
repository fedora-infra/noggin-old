from __future__ import absolute_import

from ipsilon.providers.openidc.plugins.common import OpenidCExtensionBase


class OpenidCExtension(OpenidCExtensionBase):
    name = 'caiapi'
    display_name = 'Community Account Information API'
    scopes = {
        'https://github.com/fedora-infra/noggin/testscope': {
            'display_name': 'Test scope',
            'claims': [],
        },
    }
