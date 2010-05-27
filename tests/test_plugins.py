
import gtk

from pygtkhelpers.plugins import GObjectPlugin, apply_plugins


class OkButtonPlugin(GObjectPlugin):
    """A plugin to make a button into an OK Button
    """
    plugin_name = 'ok_button'

    def create_ui(self):
        self.widget.set_use_stock(True)
        self.widget.set_label(gtk.STOCK_OK)


def test_plugin_apply():
    w = gtk.Button()
    apply_plugins(w, OkButtonPlugin)
    assert w.plugins.ok_button
    assert w.get_label() == gtk.STOCK_OK
    assert w.get_use_stock()

def test_named_plugin_apply():
    w = gtk.Button()
    apply_plugins(w, dummy=OkButtonPlugin)
    assert w.plugins.dummy
    assert w.get_label() == gtk.STOCK_OK
    assert w.get_use_stock()

def test_named_multiple_plugins_apply():
    w = gtk.Button()
    apply_plugins(w, OkButtonPlugin, dummy=OkButtonPlugin)
    assert w.plugins.dummy
    assert w.plugins.ok_button
    assert w.get_label() == gtk.STOCK_OK
    assert w.get_use_stock()


