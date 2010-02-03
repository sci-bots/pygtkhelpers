
# proxying

import gobject

from pygtkhelpers.utils import gsignal


class GObjectProxy(gobject.GObject):

    __gtype_name__ = 'PyGTKHelperGObjectProxy'

    gsignal('changed', object)

    def __init__(self, widget):
        gobject.GObject.__init__(self)
        self.widget = widget
        self.connections = []

    def block(self):
        for signal_id in self.connections:
            self.widget.handler_block(signal_id)

    def unblock(self):
        for signal_id in self.connections:
            self.widget.handler_unblock(signal_id)

    def update(self, value):
        self.update_internal(value)
        self.emit('changed', self.get_value())

    def read(self):
        return self.get_value()

    def update_internal(self, value):
        self.block()
        self.set_widget_value(value)
        self.unblock()

    def widget_changed(self):
        self.emit('changed', self.get_value())

    def set_widget_value(self, value):
        """Override"""

    def get_widget_value(self):
        """Override"""

    def connect_widget(self):
        """This should be overridden"""


class SinglePropertyGObjectProxy(GObjectProxy):

    prop_name = None

    def set_widget_value(self, value):
        return self.widget.set_property(self.prop_name, value)

    def get_widget_value(self):
        return self.widget.get_property(self.prop_name)


class GtkEntryProxy(SinglePropertyGObjectProxy):

    prop_name = 'text'

    def connect_widget(self):
        self.widget.connect('changed', self._on_changed)

    def _on_changed(self, entry):
        self.widget_changed()


