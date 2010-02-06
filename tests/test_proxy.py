
import os
import py
import gtk
from pygtkhelpers.proxy import widget_proxies, StringList
from pygtkhelpers.utils import refresh_gui

def pytest_generate_tests(metafunc):
    for widget, proxy in widget_proxies.items():
        if 'attr' in metafunc.funcargnames:
            if not getattr(proxy, 'prop_name', None):
                continue
        metafunc.addcall(id=widget.__name__, param=(widget, proxy))

def pytest_funcarg__widget(request):
    widget_type = request.param[0]
    setup_func = 'setup_'+widget_type.__name__

    if widget_type is gtk.FileChooserButton:
        widget = widget_type('Title')
    elif widget_type is gtk.LinkButton:
        widget = widget_type('')
    else:
        widget = widget_type()

    #XXX: generalize widget configuration
    if widget_type in [gtk.SpinButton, gtk.HScale, gtk.VScale]:
        widget.set_range(0, 999)

    if widget_type is gtk.ComboBox:
        model = gtk.ListStore(str, str)
        for name in ['foo', 'test']:
            model.append([name, name])
        widget.set_model(model)

    return widget

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
    gtk.SpinButton: 1,
    gtk.HScale: 100,
    gtk.VScale: 8.3,
    StringList: ['hans', 'peter'],
    gtk.ComboBox: 'test',
    gtk.FileChooserButton: __file__,
    gtk.FileChooserWidget: __file__,
    gtk.FontButton: 'Monospace 10',
    gtk.Label: 'Hello',
    gtk.Image: os.path.join(os.path.dirname(__file__),'data', 'black.png'),
    gtk.LinkButton: 'http://pida.co.uk/',
}


def test_update(proxy, value):
    proxy.update(value)


def test_update_and_read(proxy, value):
    proxy.update(value)
    refresh_gui(0.1, 0.01)
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

