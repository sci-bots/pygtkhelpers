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

def test_filechooser_open(tmpdir):
    filename = str(tmpdir.ensure('somefile.txt'))
    def before_run(dialog):
        dialog.set_current_folder(str(tmpdir))
        def idle_fun():
            dialog.response(gtk.RESPONSE_OK)
            assert dialog.select_filename(filename)
            #dialog.set_file(filename
            dialog.get_action_area().get_children()[0].emit('clicked')
        glib.idle_add(idle_fun)

    res = open(_before_run=before_run)
    assert res == filename
