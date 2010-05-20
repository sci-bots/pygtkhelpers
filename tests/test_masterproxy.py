
import gtk

from pygtkhelpers.test import CheckCalled
from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.proxy import MasterProxy, GtkEntryProxy

def test_add_proxy():
    m = MasterProxy()
    e = gtk.Entry()
    p = GtkEntryProxy(e)
    m.add_proxy('foo', p)
    check = CheckCalled(m, 'changed')
    e.set_text('a')
    refresh_gui()
    assert check.called_count == 1
    p.update('b')
    refresh_gui()
    assert check.called_count == 2

def test_add_proxy_for():
    m = MasterProxy()
    e = gtk.Entry()
    m.add_proxy_for('foo', e)
    check = CheckCalled(m, 'changed')
    e.set_text('a')
    refresh_gui()
    assert check.called_count == 1

def add_master():
    m = MasterProxy()
    e = gtk.Entry()
    m.add_proxy_for('foo', e)
    m2 = MasterProxy()
    m2.add_master(m)
    check = CheckCalled(m2, 'changed')
    e.set_text('a')
    assert check.called_count == 1

