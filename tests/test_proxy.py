import py
import gtk
from pygtkhelpers.proxy import widget_proxies

def pytest_generate_tests(metafunc):
    for widget, proxy in widget_proxies.items():
        metafunc.addcall(id=widget.__name__, param=(widget, proxy))

def pytest_funcarg__widget(request):
    return request.param[0]()

def pytest_funcarg__attr_type(request):
    widget, proxy = request.param
    return widget
    
def pytest_funcarg__attr(request):
    widget, proxy = request.param
    return proxy.prop_name
    

def pytest_funcarg__proxy(request):
    widget = request.getfuncargvalue('widget')
    return request.param[1](widget)

def pytest_funcarg__value(request):
    try:
        return widget_test_values[request.param[0]]
    except KeyError:
        py.test.skip('missing defaults for class %s'%request.param[0])

widget_test_values = {
    gtk.Entry: 'test',
    gtk.ToggleButton: True,
    gtk.CheckButton: True,
    gtk.CheckMenuItem: True,
    gtk.ColorButton: gtk.gdk.color_parse('red'),
}


def test_update(proxy, value):
    proxy.update(value)


def test_update_and_read(proxy, value):
    proxy.update(value)
    data = proxy.read()
    assert data == value


def test_update_emits_changed(proxy, value):
    data = []
    proxy.connect('changed', lambda p, d: data.append(d))
    proxy.update(value)
    print data
    assert len(data)==1

def test_widget_update_then_read(proxy, widget, attr, value):
    widget.set_property(attr, value)
    assert proxy.read() == value

def test_update_internal_wont_emit_changed(proxy, value):
    data = []
    proxy.connect('changed', lambda p, d: data.append(d))
    proxy.update_internal(value)
    print data
    assert len(data)==0
