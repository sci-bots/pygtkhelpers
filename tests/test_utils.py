
from py.test import raises as assert_raises
import gobject, gtk

from pygtkhelpers.utils import gsignal, gproperty

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
