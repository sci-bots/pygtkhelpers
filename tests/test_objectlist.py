
import py
import gtk, gtk.gdk
from pygtkhelpers.ui.objectlist import ObjectList, Column, Cell
from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.test import CheckCalled


class User(object):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __eq__(self, other):
        return self.name == other.name and self.age == other.age

user_columns = [
    Column('name', str, editable=True),
    Column('age', int),
]

def test_append():
    items = ObjectList(user_columns)
    assert len(items) == 0

    user = User(name="hans", age=10)
    items.append(user)

    assert len(items) == 1
    assert items[0] is user

    assert user in items

    #containment is identity based
    assert User(name="hans", age=10) not in items

    #dont allow the same object twice
    py.test.raises(ValueError, items.append, user)

def test_append_selected():
    items = ObjectList(user_columns)
    user = User(name="hans", age=10)
    items.append(user, select=True)

    assert items.selected_item is user

def test_append_unselected():
    items = ObjectList(user_columns)
    user = User(name="hans", age=10)
    items.append(user, select=False)
    assert items.selected_item is None

def test_select_single_fails_when_select_multiple_is_set():
    items = ObjectList(user_columns)
    user = User(name="hans", age=10)
    items.append(user)
    items.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
    py.test.raises(AttributeError, setattr, items, 'selected_item', user)
    py.test.raises(AttributeError, 'items.selected_item')
    items.selected_items = [user]
    print items.selected_items
    refresh_gui()
    assert items.selected_items == [user]



def test_extend():
    items = ObjectList(user_columns)
    items.extend([
        User('hans', 22),
        User('peter', 22),
        ])
    assert len(items)==2

def test_column_title():
    col = Column("name")
    view_col = col.create_treecolumn(None)
    assert view_col.get_title() == "Name"

    title_col = Column(title="Test", cells=[])
    title_view_col = title_col.create_treecolumn(None)
    assert title_view_col.get_title() == 'Test'
    assert len(title_view_col.get_cells()) == 0

def test_column_visiblility():
    col = Column('test')
    view_col = col.create_treecolumn(None)
    assert view_col.get_visible()

def test_column_invisiblility():
    col = Column('test', visible=False)
    view_col = col.create_treecolumn(None)
    assert not view_col.get_visible()


def test_column_width():
    col = Column('test', width=30)
    view_col = col.create_treecolumn(None)
    refresh_gui()
    assert view_col.get_sizing() == gtk.TREE_VIEW_COLUMN_FIXED
    assert view_col.get_fixed_width() == 30

def test_make_cells(): 
    col = Column(title='Test', cells=[
        Cell('name', int),
        Cell('name2', int),
        ])
    view_col = col.create_treecolumn(None)

    assert len(view_col.get_cells()) == 2

def test_column_expandable():
    col = Column('name', expand=True)
    
    treeview_column = col.create_treecolumn(None)
    assert treeview_column.props.expand

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


def test_edit_name():

    items = ObjectList(user_columns)
    user = User('hans', 10)
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


def test_selection_changed_signal():
    items = ObjectList(user_columns)
    user = User('hans', 10)
    items.append(user)
    selection_changed = CheckCalled(items, 'selection-changed')
    items.selected_item = user
    assert selection_changed.called

def test_cell_format_func():
    cell = Cell('test', format_func=str)
    assert cell.format_data(1) == '1'

def test_default_type():
    cell = Cell('test')
    assert cell.mappers[0].mappers[0].prop == 'text'

def test_pixbuf_type():
    cell = Cell('test', type=gtk.gdk.Pixbuf)
    assert cell.mappers[0].mappers[0].prop == 'pixbuf'

def test_markup():
    cell = Cell('test', use_markup=True)
    assert cell.mappers[0].mappers[0].prop == 'markup'

def test_stock_type():
    cell = Cell('test', use_stock=True)
    assert cell.mappers[0].mappers[0].prop == 'stock-id'

def test_secondary_mappers():
    cell = Cell('test', mapped={'markup': 'markup_attr'})
    m = cell.mappers[0]
    assert m.mappers[0].prop == 'text'
    assert m.mappers[0].attr == None
    assert m.mappers[1].prop == 'markup'
    assert m.mappers[1].attr == 'markup_attr'

def test_cell_ellipsize():
    import pango
    cell = Cell('test', ellipsize=pango.ELLIPSIZE_END)
    renderer = cell.create_renderer(None, None)
    el = renderer.get_property('ellipsize')
    assert el == pango.ELLIPSIZE_END



def test_left_click_event():
    items = ObjectList(user_columns)
    user = User('hans', 10)
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
    e.button = 1
    e.x, e.y = 10.0, 10.0
    item_clicked = CheckCalled(items, 'item-left-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called

def test_right_click_event():
    items = ObjectList(user_columns)
    user = User('hans', 10)
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
    e.button = 3
    item_clicked = CheckCalled(items, 'item-right-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called

def test_middle_click_event():
    items = ObjectList(user_columns)
    user = User('hans', 10)
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
    e.button = 2
    item_clicked = CheckCalled(items, 'item-middle-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called

def test_double_click_event():
    items = ObjectList(user_columns)
    user = User('hans', 10)
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk._2BUTTON_PRESS)
    e.button = 1
    item_clicked = CheckCalled(items, 'item-double-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called

