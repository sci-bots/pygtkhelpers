from pygtkhelpers.proxy import widget_proxies


def pytest_generate_tests(metafunc):
    for widget, proxy in widget_proxies.items():
        metafunc.addcall(id=widget.__name__, param=(widget, proxy))

def pytest_funcarg__widget(request):
    return request.param[0]()


def pytest_funcarg__proxy(request):
    widget = request.getfuncargvalue('widget')
    return request.param[1](widget)

def pytest_funcarg__attr(request):
    proxy = request.getfuncargvalue('proxy')
    return proxy.prop_name

def test_update(proxy):
    proxy.update('test')


def test_update_and_read(proxy):
    proxy.update('test')
    data = proxy.read()
    assert data == 'test'



