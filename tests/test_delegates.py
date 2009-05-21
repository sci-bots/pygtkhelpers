
from nose.tools import *

import gtk

from pygtkhelpers.delegates import SlaveView, MainView, BaseDelegate
from pygtkhelpers.resources import resource_manager
from pygtkhelpers.utils import refresh_gui

resource_manager.add_resource('ui', 'tests/ui')

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


class _TestUIDelegate(SlaveView):

    builder_file = 'test_slave.ui'

class _TestUIDelegate2(SlaveView):

    builder_path = 'tests/ui/test_slave.ui'

class _TestUIMainDelegate(MainView):

    builder_file = 'test_slave.ui'


def test_delegate1():
    assert_raises(NotImplementedError, _Delegate1)

def test_delegate2():
    t = _Delegate2()

def test_delegatge3():
    assert_raises(NotImplementedError, _Delegate3)

def test_no_ui_file():
    d = SlaveView()

def test_signals_list():
    d = _TestDelegate()
    assert list(d._get_all_handlers())

def test_ui_delegatge():
    d = _TestUIDelegate()
    assert hasattr(d, 'label1')

def test_ui_delegatge2():
    d = _TestUIDelegate2()
    assert hasattr(d, 'label1')

def test_ui_delegatge2():
    d = _TestUIMainDelegate()
    assert hasattr(d, 'label1')

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



