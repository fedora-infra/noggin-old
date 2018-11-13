from flask import render_template, jsonify


def documentation_viewfunc(API):
    """ Function that returns a view function to provide documentation. """
    def doc_viewfunc():
        return render_template(
            "documentation.html",
            version=API.version,
            routes=API.registered)

    return doc_viewfunc


def documentation_json_viewfunc(API):
    """ Function that returns a view function to provide JSON docs. """
    def doc_json_viewfunc():
        doc = {}

        doc['version'] = 'v%s' % API.version
        doc['operations'] = {}

        for routeurl, routeinfo in API.registered.items():
            doc['operations'][routeurl] = {}
            for method, apifunc in routeinfo.items():
                rcodes = {}
                for rcode in apifunc.return_codes:
                    rcodes[rcode[0]] = rcode[1:]
                doc['operations'][routeurl][method] = {
                    'auth': {'user': apifunc.user_auth,
                             'client': apifunc.client_auth},
                    'arguments': apifunc.arguments,
                    'return_codes': rcodes,
                }

        return jsonify(doc)

    return doc_json_viewfunc
