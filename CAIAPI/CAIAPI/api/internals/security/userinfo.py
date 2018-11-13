class UserShim(object):
    def __init__(self, token_info):
        self.token = token_info
        self.user_info = None

    def __str__(self):
        return "<UserTokenInfo(username=%s, userinfo=%s)>" % (
            self.username, self.user_info)

    @property
    def username(self):
        return self.token['sub']

    def __getattr__(self, key):
        if self.user_info and key in self.user_info:
            return self.user_info[key]

        # Let's get the user information from LDAP
        self.user_info = None

        raise ValueError("User field %s does not exist" % key)
