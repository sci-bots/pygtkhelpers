
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
