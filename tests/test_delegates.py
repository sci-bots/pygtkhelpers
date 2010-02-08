
from py.test import raises
import gtk, gobject

from pygtkhelpers.delegates import SlaveView, ToplevelView, BaseDelegate, \
    WindowView
from pygtkhelpers.utils import refresh_gui, gproperty

class _Delegate1(BaseDelegate):
    pass

class _Delegate2(BaseDelegate):

    def create_default_toplevel(self):
        pass

class _Delegate3(BaseDelegate):

    builder_file = 'test_slave.ui'

    def create_default_toplevel(self):
        pass


class _TestDelegate(SlaveView):

    def create_ui(self):
        self.clicked = False
        self.main = gtk.Button()
        self.widget.pack_start(self.main)

    def on_main__clicked(self, button):
        self.clicked = True

class _Delegate5(SlaveView):

    def create_ui(self):
        self.clicked = False
        self.main = gtk.Button()
        self.widget.pack_start(self.main)

    def after_main__clicked(self, button):
        self.clicked = True

class _Delegate6(ToplevelView):

    builder_file = 'test_slave.ui'
    toplevel_name = 'label1'

class _Delegate7(SlaveView):

    gproperty('a', int)
    gproperty('b', int)

    def set_property_b(self, value):
        self._b = value

    def get_property_b(self):
        return 17

class _TestUIDelegate(SlaveView):

    builder_file = 'test_slave.ui'

class _TestUIDelegate2(SlaveView):

    builder_path = 'tests/ui/test_slave.ui'

class _TestUIMainDelegate(ToplevelView):

    builder_file = 'test_slave.ui'

class _TestUIDelegateBindSignalError(SlaveView):
    def create_ui(self):
        self.button = gtk.Button("test")
        self.widget.pack_start(self.button)

    def on_button__clacled(self, button):
        pass

class _TestUIDelegateSignalTargetMissing(SlaveView):
    def on_button__clicked(self, button):
        pass


def test_delegate1():
    raises(NotImplementedError, _Delegate1)

def test_delegate2():
    t = _Delegate2()

def test_delegatge3():
    raises(NotImplementedError, _Delegate3)

def test_no_ui_file():
    d = SlaveView()

class MissingUiDelegate(SlaveView):
    builder_file = 'missing.ui'

class MissingUiDelegate2(SlaveView):
    builder_path = 'missing.ui'

def test_missing_uifile():
    raises(LookupError, MissingUiDelegate)

def test_missing_uipath():
    raises(LookupError, MissingUiDelegate2)


def test_signals_list():
    d = _TestDelegate()
    assert list(d._get_all_handlers())

def test_ui_delegatge():
    d = _TestUIDelegate()
    assert hasattr(d, 'label1')

def test_ui_delegatge2():
    d = _TestUIDelegate2()
    assert hasattr(d, 'label1')

def test_ui_delegatge3():
    d = _TestUIMainDelegate()
    assert hasattr(d, 'label1')





def test_ui_main_delegate_bad_toplevel():
    d = _Delegate6()
    assert gobject.type_is_a(d._toplevel, gtk.Window)

def test_signal_handle():
    d = _TestDelegate()
    d.main.clicked()
    refresh_gui()
    assert d.clicked

def test_signal_after():
    d = _Delegate5()
    d.main.clicked()
    refresh_gui()
    assert d.clicked

def test_props():
    d = _Delegate7()
    assert d.get_property('a') == 0
    d.set_property('a', 19)
    assert d.get_property('a') == 19
    d.set_property('b', 9)
    assert d._b == 9
    assert d.get_property('b') == 17

def test_bind_sinal_error_warning():
    raises(TypeError, _TestUIDelegateBindSignalError)


def test_find_signal_target_warning():
    raises(LookupError, _TestUIDelegateSignalTargetMissing)


class NeedsBaseClassUIFileSearch(_TestUIDelegate):
    __module__ = 'a.big.lie'

def test_uifile_load_from_base():
    '''
    a delegate should search base classes for ui definitions
    first match goes
    '''
    NeedsBaseClassUIFileSearch()

# slave and master
class S(SlaveView):
    def create_ui(self):
        self.entry = gtk.Entry()
        self.widget.add(self.entry)

class W(WindowView):
    def create_ui(self):
        self.slave = self.add_slave(S(), 'widget')


def test_addslave_delegate():
    w = W()
    assert len(w.slaves)

def test_slavewidget_added():
    w = W()
    assert w.widget.get_child()

def test_missing_container():
    w = WindowView()
    raises(AttributeError, w.add_slave, S(), 'banana')

