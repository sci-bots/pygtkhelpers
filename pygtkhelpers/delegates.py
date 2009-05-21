


import gobject, gtk


from .resources import resource_manager
from .utils import gsignal


def get_first_builder_window(builder):
    for obj in builder.get_objects():
        if isinstance(obj, gtk.Window):
            # first window
            return obj

class BaseDelegate(gobject.GObject):

    builder_file = None
    builder_path = None
    toplevel_name = 'main'

    def __init__(self):
        gobject.GObject.__init__(self)
        self._toplevel = None
        self._load_builder()
        if self._toplevel is None:
            self._toplevel = self.create_default_toplevel()
        self.widget = self._toplevel
        self.create_ui()
        self._connect_signals()

    def _calculate_builder_path(self):
        if self.builder_path:
            self.builder_path = os.path.abspath(self.builder_path)
        elif self.builder_file:
            self.builder_path = resource_manager.get_resource('ui', self.builder_file)

    def get_builder_toplevel(self, builder):
        raise NotImplementedError

    def create_default_toplevel(self):
        raise NotImplementedError

    def _load_builder(self):
        self._calculate_builder_path()
        if not self.builder_path:
            return
        builder = gtk.Builder()
        builder.add_from_file(self.builder_path)
        self._toplevel = self.get_builder_toplevel(builder)
        for obj in builder.get_objects():
            setattr(self, obj.get_name(), obj)

    def _connect_signals(self):
        for name in self._get_all_handlers():
            self._connect_signal(name)

    def _parse_signal_handler(self, name):
        signal_type, widget_signal = name.split('_', 1)
        widget_name, signal_name = widget_signal.split('__')
        return signal_type, widget_name, signal_name

    def _connect_signal(self, name):
        method = getattr(self, name)
        signal_type, widget_name, signal_name = self._parse_signal_handler(name)
        widget = self.get_widget(widget_name)
        if widget is None:
            raise LookupError('Widget named %s is not available.' )
        if signal_type == 'on':
            widget.connect(signal_name, method)
        elif signal_type == 'after':
            widget.connect_after(signal_name, method)

    def _get_all_handlers(self):
        for name in dir(self):
            if (name.startswith('on_') or
                    name.startswith('after_') and
                    '__' in  name):
                yield name

    def get_widget(self, name):
        return getattr(self, name, None)

    def create_ui(self):
        """
        Create additional UI here.
        """


class SlaveView(BaseDelegate):

    def get_builder_toplevel(self, builder):
        toplevel = builder.get_object(self.toplevel_name)
        if toplevel is None:
            toplevel = get_first_builder_window(builder).child
        if toplevel is not None:
            toplevel.unparent()
        return toplevel

    def create_default_toplevel(self):
        return gtk.VBox()


class MainView(BaseDelegate):

    def get_builder_toplevel(self, builder):
        toplevel = builder.get_object(self.toplevel_name)
        if toplevel is None:
            toplevel = get_first_builder_window(builder)
        return toplevel

    def create_default_toplevel(self):
        return gtk.Window()

