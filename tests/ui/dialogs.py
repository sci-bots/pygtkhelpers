import glib
from pygtkhelpers.ui.dialogs import info, error

def with_response(response, starter, *k, **kw):
    def before_run(dialog):
        def idle_fun():
            dialog.response(response)
        glib.idle_add(idle_fun)

    return starter(*k, _before_run=before_run, **kw)

def test_info():
    with_response(1, info, 'hi')
