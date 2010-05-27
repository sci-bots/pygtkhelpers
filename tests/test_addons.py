
import gtk

from pygtkhelpers.addons import GObjectPlugin, apply_addons, apply_addon


class OkButtonPlugin(GObjectPlugin):
    """A addon to make a button into an OK Button
    """
    addon_name = 'ok_button'

    def configure(self):
        self.widget.set_use_stock(True)
        self.widget.set_label(gtk.STOCK_OK)


def test_addon_apply():
    w = gtk.Button()
    apply_addons(w, OkButtonPlugin)
    assert w.addons.ok_button
    assert w.get_label() == gtk.STOCK_OK
    assert w.get_use_stock()


def test_named_addon_apply():
    w = gtk.Button()
    apply_addons(w, dummy=OkButtonPlugin)
    assert w.addons.dummy
    assert w.get_label() == gtk.STOCK_OK
    assert w.get_use_stock()


def test_named_multiple_addons_apply():
    w = gtk.Button()
    apply_addons(w, OkButtonPlugin, dummy=OkButtonPlugin)
    assert w.addons.dummy
    assert w.addons.ok_button
    assert w.get_label() == gtk.STOCK_OK
    assert w.get_use_stock()

def test_missing_addon():
    w = gtk.Button()
    apply_addons(w, OkButtonPlugin)
    assert w.addons.banana is None


class StockButtonPlugin(GObjectPlugin):
    """A addon to make a button into an any Button, or an OK button by default
    """
    addon_name = 'stock_button'

    def configure(self, stock=None):
        self.widget.set_use_stock(True)
        self.widget.set_label(stock or gtk.STOCK_OK)


def test_addon_init_values():
    w = gtk.Button()
    apply_addon(w, StockButtonPlugin, stock=gtk.STOCK_CANCEL)
    assert w.addons.stock_button
    assert w.get_label() == gtk.STOCK_CANCEL
    assert w.get_use_stock()


def test_addon_default_values():
    w = gtk.Button()
    apply_addon(w, StockButtonPlugin)
    assert w.addons.stock_button
    assert w.get_label() == gtk.STOCK_OK
    assert w.get_use_stock()



