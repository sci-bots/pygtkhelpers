
from py.test import raises
from pygtkhelpers.objectlist import ObjectList, Column, Cell


class User(object):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __eq__(self, other):
        return self.name == other.name and self.age == other.age

user_columns = [
    Column('name', str),
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
    view_col = col.make_viewcolumn(None)
    assert view_col.get_title() == "Name"

    title_col = Column(title="Test", cells=[])
    title_view_col = title_col.make_viewcolumn(None)
    assert title_view_col.get_title() == 'Test'
    assert len(title_view_col.get_cells()) == 0


def test_make_cells():
    col = Column(title='Test', cells=[
        Cell('name', int),
        Cell('name2', int),
        ])
    view_col = col.make_viewcolumn(None)

    assert len(view_col.get_cells()) == 2


