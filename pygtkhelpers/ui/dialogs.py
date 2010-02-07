# -*- coding: utf-8 -*-

"""
    pygtkhelpers.ui.dialogs
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Dialog helpers

    largely inspired by kiwi.ui.dialogs

    :copyright: 2009-2010 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

#XXX: i18n

import gtk
from functools import partial

image_types = {
    gtk.MESSAGE_INFO: gtk.STOCK_DIALOG_INFO,
    gtk.MESSAGE_WARNING : gtk.STOCK_DIALOG_WARNING,
    gtk.MESSAGE_QUESTION : gtk.STOCK_DIALOG_QUESTION,
    gtk.MESSAGE_ERROR : gtk.STOCK_DIALOG_ERROR,
}

button_types = {
    gtk.BUTTONS_NONE: (),
    gtk.BUTTONS_OK: (
        gtk.STOCK_OK,
        gtk.RESPONSE_OK,
    ),
    gtk.BUTTONS_CLOSE: (
        gtk.STOCK_CLOSE,
        gtk.RESPONSE_CLOSE,
    ),
    gtk.BUTTONS_CANCEL: (
        gtk.STOCK_CANCEL,
        gtk.RESPONSE_CANCEL,
    ),
    gtk.BUTTONS_YES_NO: (
        gtk.STOCK_NO,
        gtk.RESPONSE_NO,
        gtk.STOCK_YES,
        gtk.RESPONSE_YES,
    ),
    gtk.BUTTONS_OK_CANCEL: (
        gtk.STOCK_CANCEL,
        gtk.RESPONSE_CANCEL,
        gtk.STOCK_OK,
        gtk.RESPONSE_OK,
    ),
}

def _destroy(obj):
    #XXX: util?
    obj.destroy()
    if not gtk.main_level():
        from pygtkhelpers.utils import refresh_gui
        refresh_gui()



class AlertDialog(gtk.Dialog):
    def __init__(self, parent, flags,
                 type=gtk.MESSAGE_INFO,
                 buttons=gtk.BUTTONS_NONE,
                 ):
        #XXX: better errors
        assert type in image_types, 'not a valid type'
        assert buttons in button_types, 'not a valid set of buttons'

        gtk.Dialog.__init__(self, ' ', parent, flags)
        self.set_border_width(5)
        self.set_has_separator(False)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)

        self.primary = gtk.Label()
        self.secondary = gtk.Label()
        self.details = gtk.Label()
        self.image = gtk.image_new_from_stock(
                    image_types[type],
                    gtk.ICON_SIZE_DIALOG
                    )
        self.image.set_alignment(0.0, 0.5)
        self.primary.set_use_markup(True)

        for label in (self.primary, self.secondary, self.details):
            label.set_line_wrap(True)
            label.set_selectable(True)
            label.set_alignment(0.0, 0.5)

        hbox = gtk.HBox(False, 12)
        hbox.set_border_width(5)
        hbox.pack_start(self.image, False, False)

        self.label_vbox = vbox = gtk.VBox(False, 0)
        hbox.pack_start(vbox, False, False)
        vbox.pack_start(self.primary, False, False)
        vbox.pack_start(self.secondary, False, False)

        self.expander = gtk.expander_new_with_mnemonic(
                'show more _details'
                )
        self.expander.set_spacing(5)
        self.expander.add(self.details)
        vbox.pack_start(self.expander, False, False)
        self.vbox.pack_start(hbox, False, False)
        hbox.show_all()
        self.expander.hide()
        self._buttons = button_types[buttons]
        self.add_buttons(*self._buttons)


    def set_primary(self, text):
        #XXX: escape
        self.primary.set_markup(
                '<span weight="bold" size="larger">%s</span>'%(text,)
                )
    def set_secondary(self, text):
        self.set_secondary.set_markup(text)

    def set_details(self, text):
        self.details.set_markup(text)
        self.expander.show()

    def set_details_widget(self, widget):
        self.expander.remove(self.details)
        self.details = widget
        self.expander.add(widget)
        self.expander.show()


def _message_dialog(type, short,
                    long=None,
                    parent=None,
                    buttons=gtk.BUTTONS_OK,
                    default=None, #XXX: kiwi had -1 there, why?
                    _before_run=None): # for unittests

    if buttons in button_types:
        dialog_buttons = buttons
        buttons = []
    else:
        assert buttons is None or isinstance(buttons, tuple)
        dialog_buttons = gtk.BUTTONS_NONE

    assert parent is None or isinstance(parent, gtk.Window)


    dialog = AlertDialog(
                parent=parent,
                flags=gtk.DIALOG_MODAL,
                type=type,
                buttons = dialog_buttons,
                )
    dialog.set_primary(short)

    if long:
        #XXX: test all cases
        if isinstance(long, gtk.Widget):
            dialog.set_details_widget(long)
        elif isinstance(long, basestring):
            dialog.set_details(long)
        else:
            raise TypeError('long must be a string or a Widget, not %r'%long)

    if default is not None:
        dialog.set_default_response(default)
    if parent:
        dialog.set_transient_for(parent)
        dialog.set_modal(True)

    if _before_run is not None:
        _before_run(dialog)

    response = dialog.run()
    _destroy(dialog)
    return response


def simple(type, short, long=None,
           parent=None, buttons=gtk.BUTTONS_OK, default=None, **kw):
    if buttons == gtk.BUTTONS_OK:
        default = gtk.RESPONSE_OK
    return _message_dialog(type, short, long,
                         parent=parent, buttons=buttons,
                         default=default, **kw)

error = partial(simple, gtk.MESSAGE_ERROR)
info = partial(simple, gtk.MESSAGE_INFO)
warning = partial(simple, gtk.MESSAGE_WARNING)
yesno = partial(simple, gtk.MESSAGE_WARNING,
                default=gtk.RESPONSE_YES,
                buttons=gtk.BUTTONS_YES_NO,)



def open(title='Open', parent=None, patterns=None,
         folder=None, filter=None, _before_run=None):
    """an open dialog
    :param parent: window or None
    :param patterns: file match patterns
    :param folder: initial folder
    :param filter: file filter

    use of filter and patterns at the same time is invalid
    """

    assert not (patterns and filter)

    filechooser = gtk.FileChooserDialog(title,
                                        parent,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    if patterns or filter:
        if not filter:
            filter = gtk.FileFilter()
            for pattern in patterns:
                filter.add_pattern(pattern)
        filechooser.set_filter(filter)
    filechooser.set_default_response(gtk.RESPONSE_OK)

    if folder:
        filechooser.set_current_folder(folder)

    try:
        if _before_run is not None:
            _before_run(filechooser)
        response = filechooser.run()
        if response != gtk.RESPONSE_OK:
            return

        path = filechooser.get_filename()
        if path and os.access(path, os.R_OK):
            return path

    finally:
        _destroy(filechooser)



def ask_overwrite(filename, parent=None, **kw):
    submsg1 = 'A file named "%s" already exists' % os.path.abspath(filename)
    submsg2 = 'Do you wish to replace it with the current one?'
    text = ('<span weight="bold" size="larger">%s</span>\n'
            '\n%s\n' % (submsg1, submsg2))
    result = messagedialog(gtk.MESSAGE_ERROR, text, parent=parent,
                           buttons=((gtk.STOCK_CANCEL,
                                     gtk.RESPONSE_CANCEL),
                                    (_("Replace"),
                                     gtk.RESPONSE_YES)),
                                    **kw)
    return result == gtk.RESPONSE_YES



def save(title='Save', parent=None, current_name='', folder=None,
        _before_run=None, _before_overwrite=None):
    """Displays a save dialog."""
    filechooser = gtk.FileChooserDialog(title, parent,
                                        gtk.FILE_CHOOSER_ACTION_SAVE,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_SAVE, gtk.RESPONSE_OK))
    if current_name:
        filechooser.set_current_name(current_name)
    filechooser.set_default_response(gtk.RESPONSE_OK)

    if folder:
        filechooser.set_current_folder(folder)

    path = None
    while True:
        if _before_run:
            _before_run(filechooser)
            _before_run = None #XXX: find better implications
        response = filechooser.run()
        if response != gtk.RESPONSE_OK:
            path = None
            break

        path = filechooser.get_filename()
        if not os.path.exists(path):
            break

        if ask_overwrite(path, parent, _before_run=_before_overwrite):
            break
        _before_overwrite = None #XXX: same
    _destroy(filechooser)
    return path

