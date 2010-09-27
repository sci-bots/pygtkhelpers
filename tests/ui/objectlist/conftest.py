import gtk

from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.ui.objectlist import ObjectList, ObjectTree, Column

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
