import py
import gtk
from pygtkhelpers.utils import refresh_gui
from .conftest import User

from pygtkhelpers.test import CheckCalled

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

def test_deselect(items, user):
    items.append(user)
    items.selected_item = user
    refresh_gui()
    items.selected_item = None
    refresh_gui()

def test_deselect_multiple(items, user, user2):
    listing = [user, user2]
    items.extend(listing)
    items.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
    items.selected_items = listing
    refresh_gui()
    assert items.selected_items == listing
    items.selected_items = []
    refresh_gui()
    assert items.selected_items == []

    items.selected_items = listing
    refresh_gui()
    assert items.selected_items == listing
    items.selected_items = None
    refresh_gui()
    assert items.selected_items == []

def test_remove_missing(items, user):
    py.test.raises(ValueError, items.remove, user)

def test_selection_changed_signal(items, user):
    items.append(user)
    selection_changed = CheckCalled(items, 'selection-changed')
    items.selected_item = user
    assert selection_changed.called

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

def test_item_after(items, user, user2, user3):
    items.extend([user, user2, user3])
    assert items.item_after(user) is user2
    assert items.item_after(user2) is user3
    assert items.item_after(user3) is None

def test_item_before(items, user, user2, user3):
    items.extend([user, user2, user3])
    assert items.item_before(user2) is user
    assert items.item_before(user3) is user2
    assert items.item_before(user) is None

