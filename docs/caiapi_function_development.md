CAIAPI API Function Development
===============================

This document describes the API framework used to define functions in CAIAPI functions.

General ideas
-------------

The API framework for CAIAPI is declarative: functions add declarators that control the way they're called and what they can return.
These declarators get verified for sanity on startup of the WSGI application, so any invalid combinations should avoid the server from starting.
There are a few decorators that must always be added, specifically:
- Register: must register to at least one function/method combination
- Possible return codes: must specify at least one success response
- Client auth: must specify either `client_auth` or `no_client_auth`
- User auth: must specify either `user_auth` and a list of expected OpenIDC scopes or `no_user_auth`.

Based on the decorators, the documentation for the API is generated fully automatically.
