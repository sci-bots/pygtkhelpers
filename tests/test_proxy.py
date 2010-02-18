
import os
import py
import gtk
from pygtkhelpers.proxy import widget_proxies, StringList, SimpleComboBox
from pygtkhelpers.utils import refresh_gui

def pytest_generate_tests(metafunc):
    for widget, proxy in widget_proxies.items():
        if 'attr' in metafunc.funcargnames:
            if (not getattr(proxy, 'prop_name', None) or
                getattr(proxy, 'dprop_name', None)):
                continue
        metafunc.addcall(id=widget.__name__, param=(widget, proxy))

def pytest_funcarg__widget(request):
    'the gtk widget the proxy should use'
    widget_type = request.param[0]
    init_args = widget_initargs.get(widget_type, ())

    widget = widget_type(*init_args)
    setup = widget_setups.get(widget_type)
    if setup is not None:
        setup(widget)
    return widget

def pytest_funcarg__attr(request):
    'the property name the proxy will access on the wrapped widget'
    widget, proxy = request.param
    return proxy.prop_name

def pytest_funcarg__proxy(request):
    'the proxy object that wraps the widget'
    widget = request.getfuncargvalue('widget')
    return request.param[1](widget)

def pytest_funcarg__value(request):
    'the value the test should assign via the proxy'
    try:
        return widget_test_values[request.param[0]]
    except KeyError:
        py.test.skip('missing defaults for class %s'%request.param[0])


def add_simple_model(widget):
    model = gtk.ListStore(str, str)
    for name in ['foo', 'test']:
        model.append([name, name])
    widget.set_model(model)
    return widget

def add_range(widget):
    widget.set_range(0, 999)
    return widget

widget_initargs = {
    gtk.FileChooserButton: ('Title',),
    gtk.LinkButton: ('',),
    SimpleComboBox: ( [('name', 'Name'), ('test', "Der Test")], 'name', ),
}

widget_setups = {
    gtk.ComboBox: add_simple_model,
    gtk.SpinButton: add_range,
    gtk.HScale: add_range,
    gtk.VScale: add_range,
    gtk.HScrollbar: add_range,
    gtk.VScrollbar: add_range
}
widget_test_values = {
    gtk.Entry: 'test',
    gtk.TextView: 'test',
    gtk.ToggleButton: True,
    gtk.CheckButton: True,
    gtk.CheckMenuItem: True,
    gtk.RadioButton: True,
    gtk.ColorButton: gtk.gdk.color_parse('red'),
    gtk.SpinButton: 1,
    gtk.HScale: 100,
    gtk.VScale: 8.3,
    gtk.HScrollbar: 8.3,
    gtk.VScrollbar: 8.3,
    StringList: ['hans', 'peter'],
    gtk.ComboBox: 'test',
    SimpleComboBox: 'test',
    gtk.FileChooserButton: __file__,
    gtk.FileChooserWidget: __file__,
    gtk.FontButton: 'Monospace 10',
    gtk.Label: 'Hello',
    gtk.Image: os.path.join(os.path.dirname(__file__),'data', 'black.png'),
    gtk.LinkButton: 'http://pida.co.uk/',
    gtk.ProgressBar: 0.4,
}


def test_update(proxy, value):
    proxy.update(value)


def test_update_and_read(proxy, value):
    proxy.update(value)
    refresh_gui()
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

