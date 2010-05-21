
import gtk

from pygtkhelpers.test import CheckCalled
from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.proxy import ProxyGroup, GtkEntryProxy

def test_add_proxy():
    m = ProxyGroup()
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
    m = ProxyGroup()
    e = gtk.Entry()
    m.add_proxy_for('foo', e)
    check = CheckCalled(m, 'changed')
    e.set_text('a')
    refresh_gui()
    assert check.called_count == 1

def test_add_group():
    m = ProxyGroup()
    e = gtk.Entry()
    m.add_proxy_for('foo', e)
    m2 = ProxyGroup()
    m2.add_group(m)
    check = CheckCalled(m2, 'changed')
    e.set_text('a')
    assert check.called_count == 1

