# -*- coding: utf-8 -*-

"""
    pygtkhelpers.ui.objectlist
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    TreeViews that are object orientated, and mimic Pythonic lists

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

import itertools
import copy

import gtk, gobject

from pygtkhelpers.utils import gsignal


class ObjectTreeViewBase(gtk.TreeView):
    """Abstract base class for object-based TreeView implementations

    :param columns: A list of Column instances
    :param searchable: Whether this view is searchable
    :param sortable: Whether this view is sortable
    :param show_tooltips: Whether this view shows tooltips
    """

    gsignal('item-activated', object)
    gsignal('item-changed', object, str, object)
    gsignal('selection-changed')
    gsignal('item-left-clicked', object, gtk.gdk.Event)
    gsignal('item-right-clicked', object, gtk.gdk.Event)
    gsignal('item-middle-clicked', object, gtk.gdk.Event)
    gsignal('item-double-clicked', object, gtk.gdk.Event)
    gsignal('item-added', object)

    def __init__(self, columns=(), **kwargs):
        gtk.TreeView.__init__(self)
        #XXX: make replacable
        self.model = self.create_model()
        self.model_base = self.model
        self.model_filter = self.model.filter_new()
        self.model_sort = gtk.TreeModelSort(self.model_filter)
        self.model_tree = self.model_sort
        self.set_model(self.model_sort)
        # setup sorting
        self.sortable = kwargs.pop('sortable', True)
        #sort_func = kwargs.pop('sort_func', self._default_sort_func)
        self.searchable = kwargs.pop('searchable', True)
        self.set_enable_search(self.searchable)
        if self.searchable:
            self.set_search_column(0)
        self.columns = None
        self.set_columns(columns)
        # misc initial setup
        self.set_property('has-tooltip', kwargs.pop('show_tooltips', True))
        self._connect_internal()

    def create_model(self):
        """Create the TreeModel instance.

        This abstract method must be implemented for subclasses. The concrete
        model should be created and returned.

        :rtype: gtk.TreeModel
        """
        raise NotImplementedError

    def __len__(self):
        """Number of items in this list
        """
        return len(self.model)

    def __contains__(self, item):
        """Identity based check of membership

        :param item: The item to check membership for
        """
        return id(item) in self._id_to_iter

    def __iter__(self):
        """Iterable
        """
        for row in self.model:
            yield row[0]

    def __getitem__(self, index):
        # index can be an integer or an iter
        return self._object_at_iter(index)

    def __delitem__(self, iter): #XXX
        obj = self._object_at_iter(iter)
        del self._id_to_iter[id(obj)]
        self.model.remove(iter)

    def set_columns(self, columns):
        assert not self.columns
        self.columns = tuple(columns)
        for idx, col in enumerate(columns):
            view_col = col.create_treecolumn(self)
            view_col.set_data('pygtkhelpers::objectlist', self)
            self.append_column(view_col)
            # needs to be done after adding the column
            if col.expander:
                self.set_expander_column(view_col)
        self._id_to_iter = {}

    def _get_selected_item(self):
        """The currently selected item"""
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_SINGLE:
            raise AttributeError('selected_item not valid for select_multiple')
        model, selected = selection.get_selected()
        if selected is not None:
            return self._object_at_sort_iter(selected)

    def _set_selected_item(self, item):
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_SINGLE:
            raise AttributeError('selected_item not valid for select_multiple')
        if item is None:
            selection.unselect_all()
        else:
            giter = self._sort_iter_for(item)
            selection.select_iter(giter)
            self.set_cursor(self._path_for(item))

    selected_item = property(
            fget=_get_selected_item,
            fset=_set_selected_item,
            #XXX: fdel for deselect?
            doc=_get_selected_item.__doc__,
            )

    def _get_selected_items(self):
        """List of currently selected items"""
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_MULTIPLE:
            raise AttributeError('selected_items only valid for select_multiple')
        model, selected_paths = selection.get_selected_rows()
        result = []
        for path in selected_paths:
            result.append(model[path][0])
        return result

    def _set_selected_items(self, new_selection):
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_MULTIPLE:
            raise AttributeError('selected_items only valid for select_multiple')
        selection.unselect_all()
        if new_selection is None:
            new_selection = ()
        for item in new_selection:
            selection.select_iter(self._sort_iter_for(item))

    selected_items = property(
            fget=_get_selected_items,
            fset=_set_selected_items,
            #XXX: fdel for deselect?
            doc=_get_selected_items.__doc__,
            )

    def _get_selected_id(self):
        selected_item = self.selected_item
        selected_id = [i for i, v in enumerate(self) if v == selected_item] 
        if selected_id:
            return selected_id[0]

    def _set_selected_id(self, id):
        self.selected_item = self[id]

    selected_id = property(
            fget=_get_selected_id,
            fset=_set_selected_id,
            #XXX: fdel for deselect?
            doc=_get_selected_id.__doc__,
            )
    def _get_selected_ids(self):
        """List of currently selected ids"""
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_MULTIPLE:
            raise AttributeError('selected_ids only valid for select_multiple')
        model, selected_paths = selection.get_selected_rows()
        if selected_paths:
            return zip(*selected_paths)[0]
        else:
            return ()

    def _set_selected_ids(self, new_selection):
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_MULTIPLE:
            raise AttributeError('selected_ids only valid for select_multiple')
        selection.unselect_all()
        if new_selection is None:
            new_selection = ()
        for row_id in new_selection:
            giter = self._sort_iter_for(self[row_id])
            selection.select_iter(giter)

    selected_ids = property(
            fget=_get_selected_ids,
            fset=_set_selected_ids,
            #XXX: fdel for deselect?
            doc=_get_selected_ids.__doc__,
            )

    def clear(self):
        """Clear all the items in the list
        """
        self.model.clear()
        self._id_to_iter.clear()

    def update(self, item):
        """Manually update an item's display in the list

        :param item: The item to be updated.
        """
        self.model.set(self._iter_for(item), 0, item)

    def move_item_down(self, item):
        """Move an item down in the list.

        Essentially swap it with the item below it.

        :param item: The item to be moved.
        """
        next_iter = self._next_iter_for(item)
        if next_iter is not None:
            self.model.swap(self._iter_for(item), next_iter)

    def move_item_up(self, item):
        """Move an item up in the list.

        Essentially swap it with the item above it.

        :param item: The item to be moved.
        """
        prev_iter = self._prev_iter_for(item)
        if prev_iter is not None:
            self.model.swap(prev_iter, self._iter_for(item))

    def item_after(self, item):
        """The item after an item
        """
        next_iter = self._next_iter_for(item)
        if next_iter is not None:
            return self._object_at_iter(next_iter)

    def item_before(self, item):
        """The item before an item

        :param item: The item to get the previous item relative to
        """
        prev_iter = self._prev_iter_for(item)
        if prev_iter is not None:
            return self._object_at_iter(prev_iter)


    def set_visible_func(self, visible_func):
        """Set the function to decide visibility of an item

        :param visible_func: A callable that returns a boolean result to
                             decide if an item should be visible, for
                             example::

                                def is_visible(item):
                                    return True
        """
        self.model_filter.set_visible_func(
                self._internal_visible_func,
                visible_func,
                )
        self._visible_func = visible_func
        self.model_filter.refilter()

    def item_visible(self, item):
        """Return whether an item is visible

        :param item: The item to test visibility
        :rtype: bool
        """
        return self._visible_func(item)

    def sort_by(self, attr_or_key, direction='asc'):
        """Sort the view by an attribute or key

        :param attr_or_key: The attribute or key to sort by
        :param direction: Either `asc` or `desc` indicating the direction of
                          sorting
        """
        # work out the direction
        if direction in ('+', 'asc', gtk.SORT_ASCENDING):
            direction = gtk.SORT_ASCENDING
        elif direction in ('-', 'desc', gtk.SORT_DESCENDING):
            direction = gtk.SORT_DESCENDING
        else:
            raise AttributeError('unrecognised direction')
        if callable(attr_or_key):
            # is a key
            sort_func = self._key_sort_func
        else:
            # it's an attribute
            sort_func = self._attr_sort_func
        self.model.set_default_sort_func(sort_func, attr_or_key)
        self.model.set_sort_column_id(-1, direction)

    def search_by(self, attr_or_test):
        if callable(attr_or_test):
            self.set_search_equal_func(self._test_search_func, attr_or_test)
        else:
            self.set_search_equal_func(self._attr_search_func, attr_or_test)

    def _iter_for(self, obj):
        return self._id_to_iter[id(obj)]

    def _view_iter_for(self, obj):
        giter = self._iter_for(obj)
        return self.model_filter.convert_child_iter_to_iter(giter)

    def _sort_iter_for(self, obj):
        viter = self._view_iter_for(obj)
        return self.model_sort.convert_child_iter_to_iter(None, viter)

    def _next_iter_for(self, obj):
        return self.model.iter_next(self._iter_for(obj))

    def _prev_iter_for(self, obj):
        return self._model_iter_prev(self._iter_for(obj))

    def _path_for(self, obj):
        return self._path_for_iter(self._iter_for(obj))

    def _view_path_for(self, obj):
        return self._view_path_for_iter(self._view_iter_for(obj))

    def _view_path_for_iter(self, giter):
        return self.model_filter.get_string_from_iter(giter)

    def _path_for_iter(self, giter):
        return self.model.get_string_from_iter(giter)

    def _object_at_iter(self, iter):
        return self.model[iter][0]

    def _object_at_view_iter(self, iter):
        return self.model_filter[iter][0]

    def _object_at_sort_iter(self, iter):
        return self.model_sort[iter][0]

    def _object_at_child_sort_iter(self, iter):
        giter = self.model_sort.convert_child_iter_to_iter(None, iter)
        return self.model_sort[giter][0]

    def _object_at_path(self, path):
        return self._object_at_iter(self.model.get_iter(path))

    def _object_at_view_path(self, path):
        return self._object_at_view_iter(self.model_filter.get_iter(path))

    def _object_at_sort_path(self, path):
        return self._object_at_sort_iter(self.model_sort.get_iter(path))

    def _model_iter_prev(self, giter):
        # because it's missing, this is from pygtk faq
        # http://faq.pygtk.org/index.py?req=show&file=faq13.051.htp
        path = self.model.get_path(giter)
        position = path[-1]
        if position == 0:
            return None
        prev_path = list(path)[:-1]
        prev_path.append(position - 1)
        prev = self.model.get_iter(tuple(prev_path))
        return prev

    def _cols_for_attr(self, attr):
        return [
            col for col in self.columns
            if col.attr == attr
        ]

    def _viewcols_for_attr(self, attr):
        return [
            col for col in self.get_columns()
            if col.get_data('pygtkhelpers::column').attr == attr
        ]

    def _connect_internal(self):
        # connect internal signals
        self.connect('button-press-event', self._on_button_press_event)
        self.connect('query-tooltip', self._on_query_tooltip)
        self.connect('row-activated', self._on_row_activated)
        self.selection = self.get_selection()
        self.selection_connect = self.selection.connect(
                'changed', self._on_selection_changed)

    def _emit_for_path(self, path, event):
        item = self._object_at_sort_path(path)
        signal_map = {
            (1, gtk.gdk.BUTTON_PRESS): 'item-left-clicked',
            (3, gtk.gdk.BUTTON_PRESS): 'item-right-clicked',
            (2, gtk.gdk.BUTTON_PRESS): 'item-middle-clicked',
            (1, gtk.gdk._2BUTTON_PRESS): 'item-double-clicked',
        }
        signal_name = signal_map.get((event.button, event.type))
        if signal_name is not None:
            self.emit(signal_name, item, event.copy())

    def _on_button_press_event(self, treeview, event):
        item_spec = self.get_path_at_pos(int(event.x), int(event.y))
        if item_spec is not None:
            # clicked on an actual cell
            path, col, rx, ry = item_spec
            self._emit_for_path(path, event)

    def _on_selection_changed(self, selection):
        self.emit('selection-changed')
        self.connect('query-tooltip', self._on_query_tooltip)

    def _on_query_tooltip(self, objectlist, x, y, ktip, tooltip):
        if not self.get_tooltip_context(x, y, ktip):
            return False
        else:
            tx, ty = self.convert_widget_to_tree_coords(x, y)
            item_spec = self.get_path_at_pos(tx, ty)
            if not item_spec:
                return False
            path, column, rx, ry = item_spec
            obj = self._object_at_path(path)
            pcol = column.get_data('pygtkhelpers::column')
            return pcol.render_tooltip(tooltip, obj)

    def _on_row_activated(self, objectlist, path, column, *k):
        self.emit('item-activated', self._object_at_sort_iter(path))

    def _visible_func(self, obj):
        #XXX: this one gets dynamically replaced
        return True

    def _internal_visible_func(self, model, iter, visible_func):
        return visible_func(model[iter][0])

    def _attr_sort_func(self, model, iter1, iter2, attr):
        # how the hell is this a filter model?
        obj1 = self._object_at_iter(iter1)
        obj2 = self._object_at_iter(iter2)
        return cmp(getattr(obj1, attr, None), getattr(obj2, attr, None))

    def _key_sort_func(self, model, iter1, iter2, key):
        obj1 = self._object_at_iter(iter1)
        obj2 = self._object_at_iter(iter2)
        return cmp(key(obj1), key(obj2))

    def _attr_search_func(self, model, column, key, iter, attr):
        obj = model[iter][0]
        val = getattr(obj, attr, '')
        return not (key.lower() in str(val).lower())

    def _test_search_func(self, model, column, key, iter, test):
        obj = model[iter][0]
        return not test(obj, key)


    def scroll_to(self, obj):
        path = self._view_path_for(obj)
        self.scroll_to_cell(path)


class ObjectList(ObjectTreeViewBase):
    """An object list
    """

    __gtype_name__ = "PyGTKHelpersObjectList"

    gsignal('item-inserted', object, int)
    gsignal('item-removed', object, int)

    def remove(self, item):
        """Remove an item from the list

        :param item: The item to remove from the list.
        :raises ValueError: If the item is not present in the list.
        """
        if item not in self:
            raise ValueError('objectlist.remove(item) failed, item not in list')
        item_id = int(self._view_path_for(item))
        giter = self._iter_for(item)
        del self[giter]
        self.emit('item-removed', item, item_id)

    def create_model(self):
        return gtk.ListStore(object)

    def insert(self, position, item, select=False):
        """Insert an item at the specified position in the list.

        :param position: The position to insert the item at
        :param item: The item to be added
        :param select: Whether the item should be selected after adding
        """
        if item in self:
            raise ValueError("item %s allready in list"%item )
        modeliter = self.model.insert(position, (item,))
        self._id_to_iter[id(item)] = modeliter
        if select:
            self.selected_item = item
        self.emit('item-inserted', item, position)


    def append(self, item, select=False):
        """Add an item to the end of the list.

        :param item: The item to be added
        :param select: Whether the item should be selected after adding
        """
        if item in self:
            raise ValueError("item %s allready in list"%item )
        modeliter = self.model.append((item,))
        self._id_to_iter[id(item)] = modeliter
        if select:
            self.selected_item = item
        self.emit('item-added', item)



    def extend(self, iter):
        """Add a sequence of items to the end of the list

        :param iter: The iterable of items to add.
        """
        for item in iter:
            self.append(item)


class SubObjectTree(object):
    def __init__(self, items, item_paths):
        self.items = items
        self.item_paths = item_paths

    def copy(self):
        return copy.deepcopy(self)

    def __iter__(self):
        if self.item_paths:
            for i in range(len(self.items)):
                item_path = self.item_paths[i]
                yield self.items[i], item_path

    def __str__(self):
        return str(zip(self.items, self.item_paths))


class Node(object):
    def __init__(self, parent, item=None):
        self.item = item
        self.children = []

    def add_child(self, child):
        self.children.append(child)


class NodeTree(object):
    gsignal('test-changed')

    def __init__(self):
        self.root = Node(None)

    def _iter_children(self, node=None):
        if node is None:
            node = self.root
        if node != self.root:
            yield node
        for child in node.children:
            for child_node in self._iter_children(child):
                yield child_node


def get_node_tree(subtree):
    node_tree = NodeTree()

    nodes = {}
    for item, item_path in zip(subtree.items, subtree.item_paths):
        if len(item_path) == 1:
            parent = node_tree.root
        else:
            parent = nodes[item_path[:-1]]
        nodes[item_path] = Node(parent, item)
        parent.add_child(nodes[item_path])
    return node_tree


class ObjectTree(ObjectTreeViewBase):
    """An object tree
    """

    __gtype_name__ = "PyGTKHelpersObjectTree"

    gsignal('item-expanded', object)
    gsignal('item-collapsed', object)
    gsignal('item-inserted', object, object)
    gsignal('item-removed', object, object)

    def _connect_internal(self):
        ObjectTreeViewBase._connect_internal(self)
        self.connect('row-expanded', self._on_row_expanded)
        self.connect('row-collapsed', self._on_row_collapsed)

    def create_model(self):
        return gtk.TreeStore(object)

    def append(self, item, parent=None, select=False):
        """Add an item to the end of the list.

        :param item: The item to be added
        :param parent: The parent item to add this as a child of, or None for
                       a top-level node
        :param select: Whether the item should be selected after adding
        """
        if item in self:
            raise ValueError("item %s allready in list"%item )
        if parent is not None:
            giter = self._iter_for(parent)
        else:
            giter = None
        modeliter = self.model.append(giter, (item,))
        self._id_to_iter[id(item)] = modeliter
        if select:
            self.selected_item = item

    def extend(self, iter, parent=None):
        """Add a sequence of items to the end of the list

        :param iter: The iterable of items to add.
        :param parent: The node to add the items as a child of, or None for
                       top-level nodes.
        """
        for item in iter:
            self.append(item, parent)

    def expand_item(self, item, open_all=True):
        """Display a node as expanded

        :param item: The item to show expanded
        :param open_all: Whether all child nodes should be recursively
                         expanded.
        """
        self.expand_row(self._view_path_for(item), open_all)

    def collapse_item(self, item):
        """Display a node as collapsed

        :param item: The item to show collapsed
        """
        self.collapse_row(self._path_for(item))

    def item_expanded(self, item):
        """Return whether an item is expanded or collapsed

        :param item: The item that is queried for expanded state
        """
        return self.row_expanded(self._path_for(item))

    def _on_row_expanded(self, objecttree, giter, path):
        item = self._object_at_sort_iter(giter) 
        if item in self.selected_items:
            # Since this item was selected before expanding, select all
            # children.
            self.selection.handler_block(self.selection_connect)
            self.selected_items += self._get_children(item)
            self.selection.handler_unblock(self.selection_connect)
        return self.emit('item-expanded', self._object_at_sort_iter(giter))

    def _on_row_collapsed(self, objecttree, giter, path):
        return self.emit('item-collapsed', self._object_at_sort_iter(giter))

    def item_iter(self, item):
        return self.model[self._path_for(item)].iter

    def item_view_iter(self, item):
        return self.model_sort[self._view_path_for(item)].iter

    def item_has_child(self, item):
        if item not in self:
            raise ValueError('objectlist.item_has_child(item) failed, item not in list')
        return self.model_sort.iter_has_child(self.item_view_iter(item))

    def _iter_siblings(self, item):
        giter = self.item_view_iter(item)
        while giter:
            item = self[self.model_sort.get_path(giter)]
            for c in self._iter_children(item):
                yield c
            giter = self.model_sort.iter_next(giter)

    def _iter_children(self, item):
        yield item
        if self.item_has_child(item):
            row = self.model[self._path_for(item)]
            for i in row.iterchildren():
                for c in self._get_children(i[0]):
                    yield c

    def _get_children(self, item):
        return [c for c in self._iter_children(item)]

    def _get_selected_items(self):
        selected_items = super(ObjectTree, self)._get_selected_items()
        all_items = []
        for item in selected_items:
            if self.item_expanded(item):
                all_items.append(item)
            else:
                all_items += self._get_children(item)
        return all_items

    def insert_before(self, sibling, item, select=False):
        self._insert_sibling(self.model.insert_before, sibling, item, select)

    def insert_after(self, sibling, item, select=False):
        self._insert_sibling(self.model.insert_after, sibling, item, select)

    def _insert_sibling(self, insert_func, sibling, item, select=False):
        if item in self:
            raise ValueError("item %s allready in list"%item )
        modeliter = insert_func(None, self._iter_for(sibling), (item, ))
        row = self.model[self._path_for(sibling)]
        self._id_to_iter[id(item)] = modeliter
        item_path = self._view_path_for(item)
        if select:
            self.selected_item = item
        self.emit('item-inserted', item, item_path)

    def insert(self, parent, position, item, select=False):
        """Insert an item at the specified position in the list.

        :param position: The position to insert the item at
        :param item: The item to be added
        :param select: Whether the item should be selected after adding
        """
        if item in self:
            raise ValueError("item %s allready in list"%item )
        modeliter = self.model.insert(parent, position, (item,))
        self._id_to_iter[id(item)] = modeliter
        if select:
            self.selected_item = item
        item_path = self._view_path_for(item)
        self.emit('item-inserted', item, item_path)
        return modeliter

    def insert_subtree(self, parent_iter, position, subtree):
        # Disable selection-changed handler for insert
        self.selection.handler_block(self.selection_connect)
        node_tree = get_node_tree(subtree)
        self._insert_subtree(parent_iter, node_tree.root, position=position)
        new_subtree = self.get_subtree(subtree.items)
        self.selection.handler_unblock(self.selection_connect)
        return new_subtree

    def insert_subtree_before(self, subtree, item=None):
        return self._insert_subtree_relative(subtree, item, before=True)

    def insert_subtree_after(self, subtree, item=None):
        return self._insert_subtree_relative(subtree, item, before=False)

    def _insert_subtree_relative(self, subtree, item=None, before=False):
        if item is None:
            node_tree = get_node_tree(self.get_selected_subtree(relative=True))
            item = node_tree.root.children[-1].item
        insert_path = self.model.get_path(self.item_iter(item))
        parent = self.model[insert_path].parent
        if parent is None:
            parent_iter = None
        else:
            parent_iter = parent.iter
        position = insert_path[-1]
        if not before:
            position += 1
        return self.insert_subtree(parent_iter, position, subtree)

    def _insert_subtree(self, parent_iter, parent_node, position=None):
        if position is None:
            position = self.model.iter_n_children(parent_iter)

        for child in parent_node.children[::-1]:
            child_iter = self.insert(parent_iter, position, child.item)
            self._insert_subtree(child_iter, child)

    def remove(self, item):
        """Remove an item from the list

        :param item: The item to remove from the list.
        :raises ValueError: If the item is not present in the list.
        """
        if item not in self:
            raise ValueError('objectlist.remove(item) failed, item not in list')
        #item_id = int(self._view_path_for(item))
        item_path = self._view_path_for(item)
        giter = self._iter_for(item)
        del self[giter]
        self.emit('item-removed', item, item_path)

    def is_subtree(self, items):
        if not items:
            return True
        siblings_iter = self._iter_siblings(items[0])
        contiguous_check = (items == [i
                for i in itertools.islice(siblings_iter, len(items))])
        try:
            next_item = siblings_iter.next() 
            if len(self._path_for(next_item)) <= len(self._path_for(items[0])):
                complete_check = True
            else:
                complete_check = False
        except StopIteration:
            complete_check = True
        return contiguous_check and complete_check

    def get_selected_subtree(self, relative=False):
        return self.get_subtree(self.selected_items, relative=relative)

    def copy_selected_subtree(self):
        return self.copy_subtree(self.selected_items)

    def copy_subtree(self, items):
        subtree = self.get_subtree(items, relative=True)
        if subtree is None:
            return None
        return subtree.copy()

    def get_subtree(self, items, relative=False):
        if not items:
            return None
        
        if not self.is_subtree(items):
            raise ValueError, 'Items must make up a complete (and contiguous)'\
                    'sub-tree.'

        items = items[:]
        item_paths = [self.model.get_path(self._iter_for(i))
                for i in items]

        if relative:
            # Normalize item paths to root path (0, )
            min_depth = min([len(item_path)
                    for item_path in item_paths])
            item_paths = [item_path[min_depth - 1:]
                    for item_path in item_paths] 
            base_path = item_paths[0][0]
            for i, item_path in enumerate(item_paths):
                new_path = list(item_path)
                new_path[0] -= base_path
                item_paths[i] = tuple(new_path)

        return SubObjectTree(items, item_paths)

    def remove_items(self, items):
        # Get items sorted by model path
        sorted_items = zip(*sorted([(self.model.get_path(self.item_iter(i)), i)
                for i in items]))[1]

        # Delete items in reverse order to ensure all children are
        # removed before removing the corresponding parent.
        for item in sorted_items[::-1]:
            self.remove(item)

    def cut_selected_subtree(self):
        return self.cut_subtree(self.selected_items)

    def cut_subtree(self, items):
        subtree = self.copy_subtree(items)
        self.remove_items(items)
        return subtree

    def __iter__(self):
        """Iterable
        """
        if self:
            for item in self._iter_siblings(self[0]):
                yield item

    selected_items = property(
            fget=_get_selected_items,
            fset=ObjectTreeViewBase._set_selected_items,
            #XXX: fdel for deselect?
            doc=_get_selected_items.__doc__,
            )
