# -*- coding: utf-8 -*-

"""
    pygtkhelpers.proxy
    ~~~~~~~~~~~~~~~~~~

    Controllers for managing data display widgets.

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""


import gobject, gtk

from pygtkhelpers.utils import gsignal
from pygtkhelpers.ui.widgets import StringList, SimpleComboBox


class GObjectProxy(gobject.GObject):
    """A proxy for a gtk.Widget

    This proxy provides a common api to gtk widgets, so that they can be used
    without knowing which specific widget they are. Very useful in form
    generation.
    """
    __gtype_name__ = 'PyGTKHelperGObjectProxy'

    gsignal('changed', object)

    signal_name = None

    def __init__(self, widget):
        gobject.GObject.__init__(self)
        self.widget = widget
        self.connections = []

    # public API

    def update(self, value):
        """Update the widget's value
        """
        self.update_internal(value)
        self.emit('changed', self.get_widget_value())

    def read(self):
        """Get the widget's value
        """
        return self.get_widget_value()

    # implementor API

    def block(self):
        for signal_id in self.connections:
            self.widget.handler_block(signal_id)

    def unblock(self):
        for signal_id in self.connections:
            self.widget.handler_unblock(signal_id)

    def update_internal(self, value):
        """Update the widget's value without firing a changed signal
        """
        self.block()
        self.set_widget_value(value)
        self.unblock()

    def widget_changed(self, *args):
        """Called to indicate that a widget's value has been changed.

        This will usually be called from a proxy implementation on response to
        whichever signal was connected in `connect_widget`

        The `*args` are there so you can use this as a signal handler.
        """
        self.emit('changed', self.get_widget_value())

    def set_widget_value(self, value):
        """Set the value of the widget.

        This will update the view to match the value given. This is called
        internally, and is called while the proxy is blocked, so no signals
        are emitted from this action.

        This method should be overriden in subclasses depending on how a
        widget's value is set.
        """

    def get_widget_value(self):
        """Get the widget value.

        This method should be overridden in subclasses to return a value from
        the widget.
        """

    def connect_widget(self):
        """Perform the initial connection of the widget

        the default implementation will connect to the widgets signal
        based on self.signal_name
        """
        if self.signal_name is not None:
            # None for read only widgets
            self.widget.connect(self.signal_name, self.widget_changed)


class SinglePropertyGObjectProxy(GObjectProxy):
    """Proxy which uses a single property to set and get the value.
    """

    prop_name = None

    def set_widget_value(self, value):
        return self.widget.set_property(self.prop_name, value)

    def get_widget_value(self):
        return self.widget.get_property(self.prop_name)

class SingleDelegatedPropertyGObjectProxy(GObjectProxy):

    prop_name = None
    dprop_name = None

    def set_widget_value(self, value):
        return self.widget.get_property(self.dprop_name
            ).set_property(self.prop_name, value)

    def get_widget_value(self):
        return self.widget.get_property(self.dprop_name
            ).get_property(self.prop_name)

    def connect_widget(self):
        if self.signal_name is not None:
            # None for read only widgets
            self.widget.get_property(self.dprop_name
                ).connect(self.signal_name, self.widget_changed)


class GtkEntryProxy(SinglePropertyGObjectProxy):
    prop_name = 'text'
    signal_name = 'changed'


class GtkToggleButtonProxy(SinglePropertyGObjectProxy):
    prop_name = 'active'
    signal_name = 'toggled'


class GtkColorButtonProxy(SinglePropertyGObjectProxy):

    prop_name = 'color'
    signal_name = 'color-set'

class StringListProxy(GObjectProxy):
    signal_name = 'content-changed'

    def get_widget_value(self):
        return self.widget.value

    def set_widget_value(self, value):
        self.widget.value = value


class GtkRangeProxy(GObjectProxy):
    signal_name = 'value-changed'

    def get_widget_value(self):
        return self.widget.get_value()

    def set_widget_value(self, value):
        self.widget.set_value(value)


class GtkFileChooserProxy(GObjectProxy):
    signal_name = 'selection-changed'

    def get_widget_value(self):
        if self.widget.get_select_multiple():
            return self.widget.get_filenames()
        else:
            return self.widget.get_filename()

    def set_widget_value(self, value):
        if self.widget.get_select_multiple():
            self.widget.unselect_all()
            for filename in value:
                self.widget.select_file(filename)
        else:
            self.widget.set_filename(value)


class GtkFontButtonProxy(SinglePropertyGObjectProxy):
    signal_name = 'font-set'
    prop_name = 'font-name'


class GtkComboBoxProxy(GObjectProxy):
    signal_name = 'changed'

    def get_widget_value(self):
        return self.get_row_value(self.active_row)

    def set_widget_value(self, value):
        # what a pain in the arse
        for i, row in enumerate(self.model):
            if self.get_row_value(row) == value:
                self.widget.set_active(i)

    def connect_widget(self):
        self.widget.connect('changed', self.widget_changed)

    @property
    def active_row(self):
        return self.model[self.widget.get_active()]

    @property
    def model(self):
        return self.widget.get_model()

    def get_row_value(self, row):
        row = list(row) #XXX: that sucks
        value = row[1:]
        if not value:
            value = row[0]
        elif len(value) == 1:
            value = value[0]
        return value


class GtkTextViewProxy(SingleDelegatedPropertyGObjectProxy):

    signal_name = 'changed'
    prop_name = 'text'
    dprop_name = 'buffer'


class GtkLabelProxy(SinglePropertyGObjectProxy):
    prop_name = 'label'


class GtkImageProxy(SinglePropertyGObjectProxy):
    prop_name = 'file'


class GtkLinkButtonProxy(SinglePropertyGObjectProxy):
    prop_name = 'uri'


class GtkProgressBarProxy(SinglePropertyGObjectProxy):
    prop_name = 'fraction'



widget_proxies = {
    gtk.Entry: GtkEntryProxy,
    gtk.ToggleButton: GtkToggleButtonProxy,
    gtk.CheckButton: GtkToggleButtonProxy,
    gtk.RadioButton: GtkToggleButtonProxy,
    gtk.CheckMenuItem: GtkToggleButtonProxy,
    gtk.ColorButton: GtkColorButtonProxy,
    gtk.ComboBox: GtkComboBoxProxy,
    gtk.SpinButton: GtkRangeProxy,
    gtk.HScale: GtkRangeProxy,
    gtk.VScale: GtkRangeProxy,
    gtk.VScrollbar: GtkRangeProxy,
    gtk.HScrollbar: GtkRangeProxy,
    gtk.FileChooserButton: GtkFileChooserProxy,
    gtk.FileChooserWidget: GtkFileChooserProxy,
    gtk.FontButton: GtkFontButtonProxy,
    gtk.Label: GtkLabelProxy,
    gtk.Image: GtkImageProxy,
    gtk.LinkButton: GtkLinkButtonProxy,
    gtk.ProgressBar: GtkProgressBarProxy,
    gtk.TextView: GtkTextViewProxy,
    StringList: StringListProxy,
    SimpleComboBox: GtkComboBoxProxy,
}

