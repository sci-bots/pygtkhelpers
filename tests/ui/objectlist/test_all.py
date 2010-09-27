
import py
import gtk, gtk.gdk
from pygtkhelpers.ui.objectlist import ObjectList, Column
from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.test import CheckCalled
from mock import Mock

def test_build_simple():
    uidef = '''
        <interface>
          <object class="PyGTKHelpersObjectList" id="test">
          </object>
        </interface>
    '''
    b = gtk.Builder()
    b.add_from_string(uidef)
    objectlist = b.get_object('test')
    print objectlist
    assert isinstance(objectlist, ObjectList)

def test_edit_name(items, user):
    items.append(user)
    item_changed = CheckCalled(items, 'item-changed')

    refresh_gui()
    assert not item_changed.called
    name_cell = items.get_columns()[0].get_cells()[0]
    text_path = items._path_for(user)
    name_cell.emit('edited', text_path, 'peter')
    refresh_gui()
    assert user.name=='peter'
    assert item_changed.called


def test_left_click_event(items, user):
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
    e.button = 1
    e.x, e.y = 10.0, 10.0
    item_clicked = CheckCalled(items, 'item-left-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called
    assert item_clicked.called_count == 1

def test_right_click_event(items, user):
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
    e.button = 3
    item_clicked = CheckCalled(items, 'item-right-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called
    assert item_clicked.called_count == 1

def test_middle_click_event(items, user):
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
    e.button = 2
    item_clicked = CheckCalled(items, 'item-middle-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called
    assert item_clicked.called_count == 1

def test_double_click_event(items, user):
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk._2BUTTON_PRESS)
    e.button = 1
    item_clicked = CheckCalled(items, 'item-double-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called
    assert item_clicked.called_count == 1

@py.test.mark.tree_only
def test_tree_expander_column(items):
    assert items.get_expander_column() is items.get_columns()[-1]

@py.test.mark.list_only
def test_list_expander_column(items):
    assert items.get_expander_column() is None

@py.test.mark.tree_only
def test_expanded_signal(items, user, user2):
    items.append(user)
    items.append(user2, user)
    item_expanded = CheckCalled(items, 'item-expanded')
    items.expand_row(items._path_for(user), True)
    refresh_gui()
    assert item_expanded.called

@py.test.mark.tree_only
def test_expand_item(items, user, user2):
    items.append(user)
    items.append(user2, user)
    item_expanded = CheckCalled(items, 'item-expanded')
    items.expand_item(user)
    refresh_gui()
    assert item_expanded.called

@py.test.mark.tree_only
def test_tree_collapse_item(items, user, user2):
    items.append(user)
    items.append(user2, user)
    item_collapsed = CheckCalled(items, 'item-collapsed')
    items.expand_item(user)
    refresh_gui()
    items.collapse_row(items._path_for(user))
    refresh_gui()
    assert item_collapsed.called

@py.test.mark.tree_only
def test_list_collapse_item(items, user, user2):
    items.append(user)
    items.append(user2, user)
    item_collapsed = CheckCalled(items, 'item-collapsed')
    items.expand_item(user)
    refresh_gui()
    items.collapse_item(user)
    refresh_gui()
    assert item_collapsed.called

@py.test.mark.tree_only
def test_item_expanded(items, user, user2):
    items.append(user)
    items.append(user2, user)
    items.expand_item(user)
    refresh_gui()
    assert items.item_expanded(user)
    items.collapse_item(user)
    refresh_gui()
    assert not items.item_expanded(user)



def test_sort_by_attr_default(items):
    items.sort_by('name')
    assert items.model_sort.has_default_sort_func()

def test_sort_by_attr_asc(items, user, user2, user3):
    items.extend([user, user2, user3])
    assert items[0] is user
    assert items[1] is user2
    assert items[2] is user3
    items.sort_by('name')
    it = [i[0] for i in items.model_sort]
    assert it[0] is user2
    assert it[1] is user
    assert it[2] is user3

def test_sort_by_attr_desc(items, user, user2, user3):
    items.extend([user, user2, user3])
    assert items[0] is user
    assert items[1] is user2
    assert items[2] is user3
    items.sort_by('name', direction='desc')
    it = [i[0] for i in items.model_sort]
    assert it[0] is user3
    assert it[1] is user
    assert it[2] is user2

def _sort_key(obj):
    # key on the last letter of the name
    return obj.name[-1]

def test_sort_by_key_asc(items, user, user2, user3):
    items.extend([user, user2, user3])
    assert items[0] is user
    assert items[1] is user2
    assert items[2] is user3
    items.sort_by(_sort_key)
    it = [i[0] for i in items.model_sort]
    assert it[0] is user3
    assert it[1] is user2
    assert it[2] is user

def test_sort_by_key_desc(items, user, user2, user3):
    items.extend([user, user2, user3])
    assert items[0] is user
    assert items[1] is user2
    assert items[2] is user3
    items.sort_by(_sort_key, '-')
    it = [i[0] for i in items.model_sort]
    assert it[0] is user
    assert it[1] is user2
    assert it[2] is user3

def test_sort_by_col(items, user, user2, user3):
    items.extend([user, user2, user3])
    assert items[0] is user
    assert items[1] is user2
    assert items[2] is user3
    # simulate a click on the header
    items.model_sort.set_sort_column_id(0, gtk.SORT_ASCENDING)
    it = [i[0] for i in items.model_sort]
    assert it[0] is user2
    assert it[1] is user
    assert it[2] is user3

def test_sort_by_col_desc(items, user, user2, user3):
    items.extend([user, user2, user3])
    it = [i[0] for i in items.model_sort]
    assert it[0] is user
    assert it[1] is user2
    assert it[2] is user3
    ui = items._sort_iter_for(user)
    print items.model_sort.iter_next(ui)
    # simulate a click on the header
    items.model_sort.set_sort_column_id(0, gtk.SORT_DESCENDING)
    it = [i[0] for i in items.model_sort]
    assert it[0] is user3
    assert it[1] is user
    assert it[2] is user2

def test_sort_item_activated(items, user, user2, user3):
    items.extend([user, user2, user3])
    mock = Mock()
    items.connect('item-activated', mock.cb)
    items.emit('row-activated', '0', gtk.TreeViewColumn())
    assert mock.cb.call_args[0][1] is user

    items.sort_by('age', '-')
    items.emit('row-activated', '0', gtk.TreeViewColumn())
    assert mock.cb.call_args[0][1] is user3


