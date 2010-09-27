import gtk
from pygtkhelpers.utils import refresh_gui
from .conftest import User

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
