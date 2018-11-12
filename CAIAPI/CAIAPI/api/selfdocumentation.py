from flask import render_template

def documentation_viewfunc(API):
    """ Function that returns a view function to provide documentation. """
    def doc_viewfunc():
        return render_template(
            "documentation.html",
            version=API.version,
            routes=API.registered)

    return doc_viewfunc
