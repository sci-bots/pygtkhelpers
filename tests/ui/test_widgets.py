from py.test import importorskip
import gtk
from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.ui.widgets import StringList, AttrSortCombo
from pygtkhelpers.ui.objectlist import ObjectList

def pytest_funcarg__pl(request):
    return StringList()

def test_proxy_stringlist_create():
    pl = StringList()
    assert not pl.view.get_headers_visible()


def test_sl_set_value(pl):
    pl.value = ['a', 'b']

    assert pl.value == ['a', 'b']


def test_sl_add_button(pl):
    assert len(pl.value) == 0
    pl.add_button.clicked()
    assert pl.value == ['New Item']

def test_sl_add_selects(pl):
    pl.add_button.clicked()
    text = pl.value_entry.get_text()
    assert text == 'New Item'
    assert pl.value_entry.props.editable

def test_pl_remove_desensible(pl):
    pl.add_button.clicked()
    pl.rem_button.clicked()
    assert pl.value == []
    assert not pl.value_entry.props.sensitive
    assert not pl.value_entry.get_text()
    pl.add_button.clicked()

    assert pl.value_entry.props.sensitive



def test_pl_edit(pl):
    pl.add_button.clicked()
    pl.value_entry.set_text('test')
    assert pl.value == ['test']


def test_attrsortcombo_with_treeview():
    mock = importorskip('mock')

    ol = mock.Mock(spec=gtk.TreeView)
    model = ol.get_model.return_value = mock.Mock(spec=gtk.TreeSortable)

    sort = AttrSortCombo(ol, [
        ('name', 'Der name'),
        ('age', 'Das Alter'),
        ], 'name')

    sort_func = model.set_default_sort_func
    (func, name), kw = sort_func.call_args
    assert name == 'name'

    sort._proxy.update('age')
    (func, name), kw = sort_func.call_args
    assert name == 'age'

    sort._combo.set_active(0) # the combo is connected
    (func, name), kw = sort_func.call_args
    assert name == 'name'

    col = model.set_sort_column_id
    assert col.call_args[0] == (-1, gtk.SORT_ASCENDING)

    sort._order_button.set_active(True)
    assert col.call_args[0] == (-1, gtk.SORT_DESCENDING)

def test_attrsortcombo_with_objectlist():

    mock = importorskip('mock')

    ol = mock.Mock(spec=ObjectList)

    sort = AttrSortCombo(ol, [
        ('name', 'Der name'),
        ('age', 'Das Alter'),
        ], 'name')

    (name, order), kw = ol.sort_by.call_args
    assert name == 'name'

    sort._proxy.update('age')
    name, order = ol.sort_by.call_args[0]
    print (name, order)
    assert name == 'age'

    sort._combo.set_active(0) # the combo is connected
    name, order = ol.sort_by.call_args[0]
    assert order == gtk.SORT_ASCENDING

    sort._order_button.set_active(True)
    name, order = ol.sort_by.call_args[0]
    assert order == gtk.SORT_DESCENDING

