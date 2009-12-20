
from py.test import raises, mark
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
    raises(ValueError, items.append, user)


def test_extend():
    items = ObjectList(user_columns)
    items.extend([
        User('hans', 22),
        User('peter', 22),
        ])
    assert len(items)==2

def test_column_getattr():
    name = Cell('name', type=str)
    age = Cell('age', type=str)
    user = User('hans', 22)

    assert name.from_object(user) == 'hans'
    assert age.from_object(user) == 22


def test_column_title():
    col = Column("name")
    view_col = col.create_treecolumn(None)
    assert view_col.get_title() == "Name"

    title_col = Column(title="Test", cells=[])
    title_view_col = title_col.create_treecolumn(None)
    assert title_view_col.get_title() == 'Test'
    assert len(title_view_col.get_cells()) == 0


def test_make_cells():
    col = Column(title='Test', cells=[
        Cell('name', int),
        Cell('name2', int),
        ])
    view_col = col.create_treecolumn(None)

    assert len(view_col.get_cells()) == 2

@mark.xfail #("not yet implemented")
def test_cell_expandable():
    col = Column(title='Test', cells=[
        Cell('name', int, expand=True),
        ])


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


