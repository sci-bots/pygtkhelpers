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
from pygtkhelpers.ui.objectlist import ObjectList, Column
from pygtkhelpers.utils import MarkupMixin


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
        expander.add(scrolled(self.get_trace_view(exc, tb)))

        #XXX: add additional buttons for pastebin/bugreport

        self.show_all()


    def get_trace_view(self, exc, tb):
        olist = ObjectList([Column('markup', use_markup=True)])
        olist.set_headers_visible(False)

        while tb is not None:
            olist.append(TracebackEntry(tb))
            tb = tb.tb_next
        return olist


class TracebackEntry(MarkupMixin):
    format = (
        'File <span color="darkgreen">{filename!e}</span>,'
        ' line <span color="blue"><i>{lineno}</i></span>'
        ' in <i>{name!e}</i>\n'
        '  {line!e}'
    )

    def __init__(self, tb):
        self.frame = tb.tb_frame
        self.lineno = tb.tb_lineno
        self.code = self.frame.f_code
        self.filename = self.code.co_filename
        self.name = self.code.co_name
        linecache.checkcache(self.filename)
        line = linecache.getline(self.filename,
                                 self.lineno,
                                 self.frame.f_globals)
        self.line = line.strip() if line else None


_old_hook = None

def dialog_handler(dialog, etype, eval, trace, extra):
    if etype not in (KeyboardInterrupt, SystemExit):
        d = dialog(eval, trace, **extra)
        d.run()
        d.destroy()

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
    global _old_hook
    assert _old_hook is None

    def new_hook(etype, eval, trace):
        gobject.idle_add(dialog_handler, dialog, etype, eval, trace, extra)
        if invoke_old_hook:
            _old_hook(etype, eval, trace)

    _old_hook = sys.excepthook
    sys.excepthook = new_hook

def uninstall_hook():
    """
    uninstall our hook
    """
    sys.excepthook = _old_hook
    _old_hook = None
