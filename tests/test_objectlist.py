
import py
import gtk, gtk.gdk
from pygtkhelpers.ui.objectlist import ObjectList, ObjectTree, Column, Cell
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
    Column('expander', expander=True),
]

def pytest_generate_tests(metafunc):
    if 'items' in metafunc.funcargnames:
        if not hasattr(metafunc.function, 'tree_only'):
            metafunc.addcall(id='list', param=ObjectList)
        if not hasattr(metafunc.function, 'list_only'):
            metafunc.addcall(id='tree', param=ObjectTree)

def pytest_funcarg__items(request):
    return request.param(user_columns)

def pytest_funcarg__user(request):
    return User(name='Hans', age=10)

def pytest_funcarg__user2(request):
    return User(name='Gretel', age=11)

def test_append(items, user):
    assert len(items) == 0
    items.append(user)
    assert len(items) == 1
    assert items[0] is user
    assert user in items

    #containment is identity based
    assert User(name="hans", age=10) not in items

    #dont allow the same object twice
    py.test.raises(ValueError, items.append, user)

def test_append_selected(items, user):
    items.append(user, select=True)

    assert items.selected_item is user

def test_append_unselected(items, user):
    items.append(user, select=False)
    assert items.selected_item is None

def test_select_single_fails_when_select_multiple_is_set(items, user):
    items.append(user)
    items.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

    py.test.raises(AttributeError, 'items.selected_item = user')
    py.test.raises(AttributeError, 'items.selected_item')
    items.selected_items = [user]
    print items.selected_items
    refresh_gui()
    assert items.selected_items == [user]



def test_extend(items):
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


def test_selection_changed_signal(items, user):
    items.append(user)
    selection_changed = CheckCalled(items, 'selection-changed')
    items.selected_item = user
    assert selection_changed.called

def test_cell_format_func():
    cell = Cell('test', format_func=str)
    assert cell.format_data(1) == '1'

def test_cell_format_string():
    cell = Cell('test', format='hoo %s')
    assert cell.format_data(1) == 'hoo 1'

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

def test_cell_toggle():
    cell = Cell('test', use_checkbox=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('radio') == False

def test_cell_radio():
    cell = Cell('test', use_radio=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('radio') == True

def test_cell_radio_checkbox_both():
    # radio and checkbox, checkbox should win
    cell = Cell('test', use_checkbox=True, use_radio=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('radio') == False

def test_cell_spin():
    cell = Cell('test', type=int, use_spin=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('adjustment').get_property('lower') == 0

def test_cell_spin_digits_int():
    cell = Cell('test', type=int, use_spin=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('digits') == 0

def test_cell_spin_digits_float():
    cell = Cell('test', type=float, use_spin=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('digits') == 2

def test_cell_spin_digits():
    cell = Cell('test', type=float, use_spin=True, digits=5)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('digits') == 5

def test_cell_spin_min():
    cell = Cell('test', type=int, use_spin=True, min=5)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('adjustment').get_property('lower') == 5

def test_cell_spin_max():
    cell = Cell('test', type=int, use_spin=True, max=5)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('adjustment').get_property('upper') == 5

def test_cell_spin_step():
    cell = Cell('test', type=int, use_spin=True, step=5)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('adjustment').get_property('step-increment') == 5

def test_cell_props():
    cell = Cell('test', cell_props={'size': 100})
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('size') == 100
    


def test_left_click_event(items, user):
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
    e.button = 1
    e.x, e.y = 10.0, 10.0
    item_clicked = CheckCalled(items, 'item-left-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called

def test_right_click_event(items, user):
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
    e.button = 3
    item_clicked = CheckCalled(items, 'item-right-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called

def test_middle_click_event(items, user):
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
    e.button = 2
    item_clicked = CheckCalled(items, 'item-middle-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called

def test_double_click_event(items, user):
    items.append(user, select=True)
    e = gtk.gdk.Event(gtk.gdk._2BUTTON_PRESS)
    e.button = 1
    item_clicked = CheckCalled(items, 'item-double-clicked')
    items._emit_for_path((0,), e)
    refresh_gui()
    assert item_clicked.called

@py.test.mark.tree_only
def test_expander_column(items):
    assert items.get_expander_column() is items.get_columns()[-1]

@py.test.mark.list_only
def test_expander_column(items):
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
def test_collapse_item(items, user, user2):
    items.append(user)
    items.append(user2, user)
    item_collapsed = CheckCalled(items, 'item-collapsed')
    items.expand_item(user)
    refresh_gui()
    items.collapse_row(items._path_for(user))
    refresh_gui()
    assert item_collapsed.called

@py.test.mark.tree_only
def test_collapse_item(items, user, user2):
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



class MockTooltip(object):

    def set_text(self, text):
        self.text = text

    def set_markup(self, markup):
        self.markup = markup

    def set_custom(self, custom):
        self.custom = custom

    def set_icon(self, icon):
        self.pixbuf = icon

    def set_icon_from_stock(self, stock, size):
        self.stock = stock
        self.size = size

    def set_icon_from_icon_name(self, iconname, size):
        self.iconname = iconname
        self.size = size


class Fruit(object):

    attr = 'value'

def test_tooltip_type_text_value():
    c = Column('test', tooltip_value='banana')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.text == 'banana'

def test_tooltip_type_text_attr():
    c = Column('test', tooltip_attr='attr')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.text == 'value'

def test_tooltip_type_markup_value():
    c = Column('test', tooltip_value='banana', tooltip_type='markup')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.markup == 'banana'

def test_tooltip_type_markup_attr():
    c = Column('test', tooltip_attr='attr', tooltip_type='markup')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.markup == 'value'

def test_tooltip_type_stock_value():
    c = Column('test', tooltip_value='banana', tooltip_type='stock')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.stock == 'banana'

def test_tooltip_type_stock_attr():
    c = Column('test', tooltip_attr='attr', tooltip_type='stock')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.stock == 'value'

def test_tooltip_type_iconname_value():
    c = Column('test', tooltip_value='banana', tooltip_type='iconname')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.iconname == 'banana'

def test_tooltip_type_iconname_attr():
    c = Column('test', tooltip_attr='attr', tooltip_type='iconname')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.iconname == 'value'

def test_tooltip_type_pixbuf_value():
    c = Column('test', tooltip_value='banana', tooltip_type='pixbuf')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.pixbuf == 'banana'

def test_tooltip_type_pixbuf_attr():
    c = Column('test', tooltip_attr='attr', tooltip_type='pixbuf')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.pixbuf == 'value'

def test_tooltip_type_custom_value():
    c = Column('test', tooltip_value='banana', tooltip_type='custom')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.custom == 'banana'

def test_tooltip_type_custom_attr():
    c = Column('test', tooltip_attr='attr', tooltip_type='custom')
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.custom == 'value'

def test_tooltip_image_size():
    c = Column('test', tooltip_attr='attr', tooltip_type='iconname',
                tooltip_image_size=gtk.ICON_SIZE_MENU)
    t = MockTooltip()
    o = Fruit()
    c.render_tooltip(t, o)
    assert t.iconname == 'value'
    assert t.size == gtk.ICON_SIZE_MENU

