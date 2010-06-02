import glib
from pygtkhelpers.ui.dialogs import info, error, open, select_folder
from pygtkhelpers.utils import refresh_gui
import gtk
import py

def with_response(response, starter, *k, **kw):
    def before_run(dialog):
        def idle_fun():
            dialog.response(response)
        glib.idle_add(idle_fun)

    return starter(*k, _before_run=before_run, **kw)

def test_info():
    with_response(1, info, 'hi')

@py.test.mark.xfail(reason='no idea how to argument filechooser dialog')
def test_filechooser_open(tmpdir):
    filename = str(tmpdir.ensure('somefile.txt'))
    def before_run(dialog):
        def idle_fun():
            dialog.emit('response', gtk.RESPONSE_OK)
            dialog.set_filename(filename)
            dialog.response(gtk.RESPONSE_OK)
            dialog.hide()
            dialog.response(gtk.RESPONSE_OK)

        glib.idle_add(idle_fun)

    res = open(_before_run=before_run)
    assert res == filename
