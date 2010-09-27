import py
from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.test import CheckCalled

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


