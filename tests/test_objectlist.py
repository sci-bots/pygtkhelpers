from pygtkhelpers.objectlist import ObjectList, Column


class User(object):
    def __init__(self, name, age):
        self.name = name
        self.age = age

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
