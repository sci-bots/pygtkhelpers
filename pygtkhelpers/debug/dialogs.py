"""
    pygtkhelpers.debug.dialogs
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    An exception handler for pygtk with nice ui

    :copyright: 2009 by Ronny Pfannschmidt <Ronny.Pfannschmidt@gmx.de>
    :license: LGPL2 or later
"""

import sys
import traceback
import linecache
from cgi import escape

import gtk
import gobject


def scrolled(widget, shadow=gtk.SHADOW_NONE):
    window = gtk.ScrolledWindow()
    window.set_shadow_type(shadow)
    window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    if widget.set_scroll_adjustments(window.get_hadjustment(),
                                      window.get_vadjustment()):
        window.add(widget)
    else:
        window.add_with_viewport(widget)
    return window


class SimpleExceptionDialog(gtk.MessageDialog):
    def __init__(self, exc, tb, parent=None, **extra):

        gtk.MessageDialog.__init__(self,
                buttons=gtk.BUTTONS_CLOSE,
                type=gtk.MESSAGE_ERROR,
                parent=parent
                )

        self.extra = extra
        self.exc = exc
        self.tb = tb

        self.set_resizable(True)

        text = 'An exception Occured\n\n<b>%s</b>: %s'
        self.set_markup(text%(exc.__class__.__name__, exc))

        #XXX: add support for showing url's for pastebins

        expander = gtk.Expander("Exception Details")
        self.vbox.pack_start(expander)
        expander.add(self.get_trace_view(exc, tb))

        #XXX: add additional buttons for pastebin/bugreport

        self.show_all()


    def get_trace_view(self, exc, tb):
        text = traceback.format_exception(type(exc), exc, tb)
        textview = gtk.TextView()
        textview.get_buffer().set_text(''.join(text))
        return scrolled(textview)



def extract_tb(tb, limit=None):
    if limit is None and hasattr(sys, 'tracebacklimit'):
        limit = sys.tracebacklimit
    assert limit is None or limit>0

    while tb is not None and (limit is None or limit >0):
        frame = tb.tb_frame
        lineno = tb.tb_lineno
        code = frame.f_code
        filename = code.co_filename
        name = code.co_name
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, frame.f_globals)
        line = line.strip() if line else None
        yield filename, lineno, name, line, frame
        tb = tb.tb_next


class ExtendedExceptionDialog(SimpleExceptionDialog):
    format = ('File <span color="darkgreen">%r</span>,'
              ' line <span color="blue"><i>%d</i></span> in <i>%s</i>\n'
              '  %s')
    def get_trace_view(self, exc, tb):
        store = gtk.ListStore(str, int, str, str, object)
        for item in extract_tb(tb):
            store.append(item)

        view = gtk.TreeView(model=store)
        view.set_headers_visible(False)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Pango Markup', cell, markup=0)
        view.append_column(column)
        column.set_cell_data_func(cell, self.data_func)
        return view

    def data_func(self, column, cell, model, iter):
        filename = escape(model.get_value(iter, 0))
        lineno = model.get_value(iter, 1)
        name = escape(model.get_value(iter, 2))
        line = escape(model.get_value(iter, 3))

        text = self.format%(filename, lineno, name, line)
        cell.set_property('markup', text)


_hook_installed = False

def install_hook(
        dialog=SimpleExceptionDialog,
        invoke_old_hook=False,
        **extra):
    """
    install the configured exception hook wrapping the old exception hook

    don't use it twice

    :oparam dialog: a different exception dialog class
    :oparam invoke_old_hook: should we invoke the old exception hook?
    """
    global _hook_installed
    old_hook = sys.excepthook

    def new_hook(etype, eval, trace):
        def handler(etype, eval, trace):
            if etype not in (KeyboardInterrupt, SystemExit):
                d = dialog(eval, trace, **extra)
                d.run()
                d.destroy()
        gobject.idle_add(handler, etype, eval, trace)
        if invoke_old_hook:
            old_hook(etype, eval, trace)
    assert not _hook_installed
    sys.excepthook = new_hook
    _hook_installed = True

