
from py.test import raises as assert_raises
import gobject, gtk

from pygtkhelpers.utils import gsignal, gproperty, \
        GObjectUserDataProxy, \
        eformat, MarkupMixin, XFormatter

from pygtkhelpers.delegates import BaseDelegate

def test_gsignal():

    class T1(gobject.GObject):
        __gtype_name__ = 'test1'
        gsignal('testsignal')
        gsignal('b', retval=gobject.TYPE_INT)
        assert_raises(TypeError, gsignal, 'c', retval=gobject.TYPE_INT, flags=gobject.SIGNAL_RUN_FIRST)

    class T3(gtk.Button):
        gsignal('clicked', 'override')

    t = T1()
    t.connect('testsignal', lambda *a: None)


def test_gproperty():

    class T2(BaseDelegate):

        def create_default_toplevel(self):
            return

        __gtype_name__ = 'test2'
        gproperty('a', int, default=0)
        assert_raises(TypeError, gproperty, 'b', bool)
        assert_raises(TypeError, gproperty, 'c', bool, default='a')
        assert_raises(TypeError, gproperty, 'd', bool, nick=1)
        assert_raises(TypeError, gproperty, 'e', bool, blurb=1)
        gproperty('f', int, default=10)
        gproperty('g', bool, default=True)
        assert_raises(TypeError, gproperty, 'h', gtk.ArrowType)
        gproperty('i', gtk.ArrowType, default=gtk.ARROW_UP)
        assert_raises(TypeError, gproperty, 'j', gtk.ArrowType, default=1)
        gproperty('k', str)
        gproperty('l', object)
        assert_raises(TypeError, gproperty, 'm', object, default=1)
        assert_raises(NotImplementedError, gproperty, 'n', gtk.Label)
        assert_raises(TypeError, gproperty, 'o', int, flags=-1)
        gproperty('p', object)

    t = T2()
    print t
    assert t.get_property('a') == 0


def test_data_proxy_set():
    w = gtk.Entry()
    data = GObjectUserDataProxy(w)
    data.foo = 123
    assert w.get_data('foo') == 123

def test_data_proxy_get():
    w = gtk.Entry()
    w.set_data('foo', 123)
    data = GObjectUserDataProxy(w)
    assert data.foo == 123

def test_data_proxy_missing():
    w = gtk.Entry()
    data = GObjectUserDataProxy(w)
    assert data.foo is None

def test_data_proxy_delete():
    w = gtk.Entry()
    data = GObjectUserDataProxy(w)
    data.foo = 123
    assert data.foo == 123
    del data.foo
    assert data.foo is None


def test_eformat():
    assert eformat('{self!e}', self='<') == '&lt;'


def test_markup_mixin_obj():
    class Tested(MarkupMixin):
        format = '{a} 1'
        a = 1
    instance = Tested()

    assert instance.markup == '1 1'

def test_markup_mixing_kwargs():
    class Tested(MarkupMixin):
        format = '{a} 1'
        a = 2 # markup kwargs should override attributes
        def markup_kwargs(self):
            return {'a': '1'}

    instance = Tested()

    assert instance.markup == '1 1'

def test_xformatter_extraconverters():
    formatter = XFormatter(a=lambda x: str(x)*2)
    result = formatter.format('{0!a}', 'x')
    assert result=='xx'

def test_markup_mixin_extra_formatter():
    class Tested(MarkupMixin):
        format = '{a!c}'
        markup_converters = {
            'c': lambda x: x.capitalize(),
        }
        a = 'a'


    instance = Tested()
    assert instance.markup == 'A'
