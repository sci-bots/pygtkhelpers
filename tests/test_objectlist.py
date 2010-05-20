
import py
import gtk, gtk.gdk
from pygtkhelpers.ui.objectlist import ObjectList, ObjectTree, Column, Cell
from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.test import CheckCalled
from mock import Mock

class User(object):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __eq__(self, other):
        return self.name == other.name and self.age == other.age

user_columns = [
    Column('name', str, editable=True, searchable=True),
    Column('age', int),
    Column('expander', expander=True),
]

def pytest_generate_tests(metafunc):
    if ('items' in metafunc.funcargnames or
        'searchcheck' in metafunc.funcargnames):
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

def pytest_funcarg__user3(request):
    return User(name='Witch', age=409)

def pytest_funcarg__searchcheck(request):
    items = request.getfuncargvalue('items')
    return SearchChecker(items)

class SearchChecker(object):
    def __init__(self, ol):
        self.ol = ol
        self.entry = gtk.Entry()
        self.ol.set_search_entry(self.entry)
        self.w = gtk.Window()
        vb = gtk.VBox()
        self.w.add(vb)
        vb.pack_start(self.ol)
        vb.pack_start(self.entry)
        self.ol.extend([
            User(name='a', age=1),
            User(name='B', age=2),
            User(name='c', age=3),
        ])
        self.u1, self.u2, self.u3 = tuple(ol)

    def assert_selects(self, key, item):
        self.entry.set_text(key)
        refresh_gui()
        assert self.ol.selected_item is item

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
    refresh_gui()
    assert items.selected_items == [user]

def test_extend(items):
    items.extend([
        User('hans', 22),
        User('peter', 22),
        ])
    assert len(items)==2

def test_remove(items, user):
    items.append(user)
    assert user in items
    items.remove(user)
    assert user not in items

def test_remove_missing(items, user):
    py.test.raises(ValueError, items.remove, user)

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

def test_cell_progress():
    cell = Cell('test', type=int, use_progress=True)
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('pulse') < 1

def test_cell_progress_text():
    cell = Cell('test', type=int, use_progress=True, progress_text='hello')
    renderer = cell.create_renderer(None, None)
    assert renderer.get_property('text') == 'hello'

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

def test_move_item_up(items, user, user2):
    items.append(user)
    items.append(user2)
    items.move_item_up(user2)
    assert items._object_at_iter(0) is user2
    assert items._object_at_iter(1) is user

def test_move_item_down(items, user, user2):
    items.append(user)
    items.append(user2)
    items.move_item_down(user)
    assert items._object_at_iter(0) is user2
    assert items._object_at_iter(1) is user

def test_move_first_item_up(items, user, user2):
    items.append(user)
    items.append(user2)
    items.move_item_up(user)
    assert items._object_at_iter(0) is user
    assert items._object_at_iter(1) is user2

def test_move_last_item_down(items, user, user2):
    items.append(user)
    items.append(user2)
    items.move_item_down(user2)
    assert items._object_at_iter(0) is user
    assert items._object_at_iter(1) is user2

@py.test.mark.tree_only
def test_move_subitem_down(items, user, user2, user3):
    items.append(user)
    items.append(user2, parent=user)
    items.append(user3, parent=user)
    items.move_item_down(user2)
    assert (items._path_for(user2) ==
            items._path_for_iter(items._next_iter_for(user3)))

@py.test.mark.tree_only
def test_move_last_subitem_down(items, user, user2, user3):
    items.append(user)
    items.append(user2, parent=user)
    items.append(user3, parent=user)
    items.move_item_down(user3)
    assert (items._path_for(user3) ==
            items._path_for_iter(items._next_iter_for(user2)))

@py.test.mark.tree_only
def test_move_subitem_up(items, user, user2, user3):
    items.append(user)
    items.append(user2, parent=user)
    items.append(user3, parent=user)
    items.move_item_up(user3)
    assert (items._path_for(user2) ==
            items._path_for_iter(items._next_iter_for(user3)))

@py.test.mark.tree_only
def test_move_last_subitem_up(items, user, user2, user3):
    items.append(user)
    items.append(user2, parent=user)
    items.append(user3, parent=user)
    items.move_item_up(user2)
    assert (items._path_for(user3) ==
            items._path_for_iter(items._next_iter_for(user2)))

def test_view_iters(items, user, user2, user3):
    items.extend([user, user2, user3])
    items.set_visible_func(lambda obj: obj.age<100)
    refresh_gui()
    assert items.item_visible(user)
    assert not items.item_visible(user3)

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

def test_search_col(searchcheck):
    searchcheck.assert_selects('a', searchcheck.u1)

def test_search_col_insensitive(searchcheck):
    searchcheck.assert_selects('A', searchcheck.u1)

def test_search_col_missing(searchcheck):
    searchcheck.assert_selects('z', None)

def test_search_col_last(searchcheck):
    searchcheck.assert_selects('c', searchcheck.u3)

def test_search_attr(searchcheck):
    searchcheck.ol.search_by('age')
    searchcheck.assert_selects('1', searchcheck.u1)

def test_search_attr_missing(searchcheck):
    searchcheck.ol.search_by('age')
    searchcheck.assert_selects('z', None)

def _search_func(item, key):
    return item.age == 1

def test_search_func(searchcheck):
    searchcheck.ol.search_by(_search_func)
    searchcheck.assert_selects('z', searchcheck.u1)

def _search_missing_func(item, key):
    return item.age == 9

def test_search_missing_func(searchcheck):
    searchcheck.ol.search_by(_search_missing_func)
    searchcheck.assert_selects('z', None)

def test_item_after(items, user, user2, user3):
    items.extend([user, user2, user3])
    assert items.item_after(user) is user2
    assert items.item_after(user2) is user3

def test_item_before(items, user, user2, user3):
    items.extend([user, user2, user3])
    assert items.item_before(user2) is user
    assert items.item_before(user3) is user2

