from argparse import ArgumentParser
import functools
import json
import sys
import os

from caiclient import CAIClient


def run_operation_method(client, args):
    method = args.pop("method")
    operation = args.pop("operation")
    args.pop("func")
    resp = client(operation, method, args)
    print("Return value: %s" % resp)


def create_oper_method_parser(client, parser, info):
    parser.set_defaults(func=run_operation_method)
    for arg in info["arguments"]:
        argname = arg["name"]
        if not arg["required"]:
            argname = "--%s" + argname
        parser.add_argument(argname, help=arg["description"])


def generate_subparsers_oper(client, parser, operinfo):
    subparsers = parser.add_subparsers()

    for method, info in operinfo.items():
        method_parser = subparsers.add_parser(method.lower(), help='TODO')
        method_parser.set_defaults(method=method)
        create_oper_method_parser(client, method_parser, info)


def full_authorize(client, args):
    scopes = set()
    for _, operinfo in client.api_definition["operations"].items():
        for _, info in operinfo.items():
            if info["auth"]["user"] is not False:
                scopes.update(info["auth"]["user"])
    token = client.oidc_client.get_token(list(scopes))
    if token is None:
        raise SystemExit("Failure getting token")
    print(token)


def generate_special_parser(client, parser):
    subparsers = parser.add_subparsers()

    # full_authorize
    full_authorize_parser = subparsers.add_parser(
        "full_authorize",
       help="Get token for all operations")
    full_authorize_parser.set_defaults(func=full_authorize)


def generate_subparsers(client, parser, operations):
    subparsers = parser.add_subparsers()

    special_parser = subparsers.add_parser("special", help="Client internals")
    generate_special_parser(client, special_parser)

    for oper, operinfo in operations.items():
        oper_parser = subparsers.add_parser(oper, help='TODO')
        oper_parser.set_defaults(operation=oper)
        generate_subparsers_oper(client, oper_parser, operinfo)


def run():
    # TODO: Implement config for this
    with open("/data/caiapi-noggin/caiclient_client.json", "r") as oidcf:
        oidc = json.loads(oidcf.read())["web"]
    server = os.getenv("CAICLIENT_SERVER", "https://caiapi.noggindev.local/")
    apiver = os.getenv("CAICLIENT_API_VERSION")
    oidc_client_info = {
        "app_identifier": "caiclient",
        "id_provider": "https://ipsilon.noggindev.local/openidc/",
        "id_provider_mapping": {"Token": "Token",
                                "Authorization": "Authorization"},
        "client_id": oidc["client_id"],
        "client_secret": oidc["client_secret"],
    }
    client = CAIClient(server,
                       client_info={"name": "caiclient",
                                    "secret": "0123456789abcdef"},
                       api_version=apiver,
                       oidc_client_info=oidc_client_info)

    main_parser = ArgumentParser(description='CAIClient')
    generate_subparsers(client,
                        main_parser,
                        client.api_definition["operations"])
    args = vars(main_parser.parse_args())

    if 'func' in args:
        args['func'](client, args)
    else:
        main_parser.print_help()
        sys.exit(1)
