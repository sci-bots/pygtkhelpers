# -*- coding: utf-8 -*-

"""
    pygtkhelpers.ui.objectlist
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    TreeViews that are object orientated, and mimic Pythonic lists

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk, gobject

from pygtkhelpers.utils import gsignal


class PropertyMapper(object):

    def __init__(self, cell, prop, attr=None):
        self.cell = cell
        self.prop = prop
        self.attr = attr
        # Check to see if this is the primary attribute, and also there is
        # format string, we do this once, so we don't check on every update.
        self.format = (attr is None) and (cell.format or cell.format_func)

    def __call__(self, cell, obj, renderer):
        value = getattr(obj, self.attr or cell.attr)
        if self.format:
            value = self.cell.format_data(value)
        renderer.set_property(self.prop, value)


class CellMapper(object):

    def __init__(self, cell, map_spec):
        self.cell = cell
        self.mappers = []
        for prop, attr in map_spec.items():
            self.mappers.append(PropertyMapper(cell, prop, attr))

    def __call__(self, cell, obj, renderer):
        for mapper in self.mappers:
            mapper(cell, obj, renderer)


class Cell(object):

    def __init__(self, attr, type=str, **kw):
        # ok this is evil, but let the individual cells use it without it
        # being tagged on the cell.
        self.kwargs = kw

        # attribute and type
        self.attr = attr
        self.type = type

        # behaviour
        self.editable = kw.get('editable', False)
        self.choices = kw.get('choices', [])

        # display
        self.use_markup = kw.get('use_markup', False)
        self.use_stock = kw.get('use_stock', False)
        self.use_checkbox = kw.get('use_checkbox', False)
        self.use_radio = kw.get('use_radio', False)
        self.use_spin = kw.get('use_spin', False)
        self.use_progress = kw.get('use_progress', False)

        # formatting
        self.format = kw.get('format')
        self.format_func = kw.get('format_func')

        self.cell_props = kw.get('cell_props', {})

        # attribute/property mapping
        self.mappers = kw.get('mappers')
        self.mapped = kw.get('mapped')


        if not self.mappers:
            self.mappers = []
            map_spec = {}
            primary_prop = self._calculate_primary_prop()
            if primary_prop:
                map_spec[primary_prop] = None
            if self.mapped:
                map_spec.update(self.mapped)
            self.mappers.append(CellMapper(self, map_spec))

    @property
    def primary_mapper(self):
        return self.mappers[0]

    def render(self, object, cell):
        for mapper in self.mappers:
            mapper(self, object, cell)

    def cell_data_func(self, column, cell, model, iter):
        obj = model.get_value(iter, 0)
        self.render(obj, cell)

    def format_data(self, data):
        if self.format:
            data = self.format % data
        elif self.format_func:
            data = self.format_func(data)
        return data

    def create_renderer(self, column, objectlist):
        #XXX: extend to more types
        if self.use_stock or self.type == gtk.gdk.Pixbuf:
            cell = gtk.CellRendererPixbuf()
        elif self.use_checkbox or self.use_radio:
            cell = CellRendererToggle(self, objectlist)
        elif self.use_progress:
            cell = CellRendererProgress(self, objectlist)
        elif self.use_spin:
            cell = CellRendererSpin(self, objectlist)
        elif self.choices:
            #XXX: a mapping?
            cell = CellRendererCombo(self, objectlist, self.choices)
        else:
            cell = CellRendererText(self, objectlist)
        cell.set_data('pygtkhelpers::cell', self)
        for prop, value in self.cell_props.items():
            cell.set_property(prop, value)
        return cell

    def _calculate_primary_prop(self):
        if self.use_stock:
            primary_prop = 'stock-id'
        elif self.type==gtk.gdk.Pixbuf:
            primary_prop = 'pixbuf'
        elif self.use_checkbox or self.use_radio:
            primary_prop = 'active'
        elif self.use_progress:
            primary_prop = 'value'
        elif self.use_markup:
            primary_prop = 'markup'
        else:
            # Includes: CellRendererText, CellRendererSpin
            primary_prop = 'text'
        return primary_prop

    def __repr__(self):
        return '<Cell %s %r>'%(self.attr, self.type)



class Column(object):
    """A Column for an ObjectList.

    A column loosely combines a GUI TreeView column with an attribute of an
    instance. The column encapsulates the type of the attribute, how it is
    displayed, whether fields are editable, the column headings, whether
    sorting can be applied, and other features.

    The mapping between columns and attributes is not exactly correct as there
    is the flexibility to add multiple cells per column.

    :param attr: The attribute to display from the object
    :param type: The Python type of the data for this attribute
    :param title: The header title for the column
    :param visible: Whether this column should be displayed
    :param width: The width of this column
    :param expand: Whether this column should expand to fit available space
    :param sorted: Whether this column should be sorted
    :param sort_key: The sort key to sort by this column
    :param sort_func: The function to sort this column by
    :param searchable: Whether this field is searchable
    :param search_key: The key used to search this column
    :param expander: Whether the expander should be shown before this column
    :param cells: A list of Cell instances to display in this colum
    :param tooltip_attr: An attribute that will display the tooltip for this
                         column
    :param tooltip_type: The type of tooltip for this column
    :param tooltip_value: The static value of the tooltip for this column
    :param tooltip_image_size: The size of an image tooltip

    """
    #XXX: handle cells properly

    def __init__(self, attr=None, type=str, title=None, **kwargs):

        #XXX: better error messages
        assert title or attr, "Columns need a title or an attribute to infer it"
        assert attr or 'cells' in kwargs, 'Columns need a attribute or a set of cells'

        self.title = title or attr.capitalize()
        self.attr = attr
        self.sorted = kwargs.pop('sorted', True)
        self.expand = kwargs.pop('expand', None)
        self.visible = kwargs.pop('visible', True)
        self.width = kwargs.pop('width', None)
        self.expander = kwargs.pop('expander', None)
        self.sort_key = kwargs.pop('sort_key', None)
        self.sort_func = kwargs.pop('sort_func', cmp)
        # tooltips are per column, not per cell
        self._init_tooltips(**kwargs)
        self.searchable = kwargs.pop('searchable', False)
        self.search_key = kwargs.pop('search_key', None)
        if 'cells' in kwargs:
            self.cells = kwargs['cells']
        else:
            #XXX: sane arg filter
            self.cells = [Cell(attr, type, **kwargs)]

    def create_treecolumn(self, objectlist):
        """Create a gtk.TreeViewColumn for the configuration.
        """
        col = gtk.TreeViewColumn(self.title)
        col.set_data('pygtkhelpers::objectlist', objectlist)
        col.set_data('pygtkhelpers::column', self)
        col.props.visible = self.visible
        if self.expand is not None:
            col.props.expand = self.expand
        if self.width is not None:
            col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            col.set_fixed_width(self.width)
        for cell in self.cells:
            view_cell = cell.create_renderer(self, objectlist)
            view_cell.set_data('pygtkhelpers::column', self)
            #XXX: better control over packing
            col.pack_start(view_cell)
            col.set_cell_data_func(view_cell, cell.cell_data_func)
        col.set_reorderable(True)
        col.set_sort_indicator(False)
        col.set_sort_order(gtk.SORT_DESCENDING)
        if objectlist and objectlist.sortable and self.sorted:
            idx = objectlist.columns.index(self)
            sort_func = self._default_sort_func
            objectlist.model_sort.set_sort_func(idx, sort_func, objectlist)
            col.set_sort_column_id(idx)
        if objectlist and objectlist.searchable and self.searchable:
            ###
            self.search_by(objectlist)
        col.connect('clicked', self._on_viewcol_clicked)
        return col

    def _init_tooltips(self, **kw):
        self.tooltip_attr = kw.get('tooltip_attr')
        self.tooltip_type = kw.get('tooltip_type', TOOLTIP_TEXT)
        if self.tooltip_type not in TOOLTIP_TYPES:
            raise ValueError('Tooltip types must be in %r.' % TOOLTIP_TYPES)
        self.tooltip_value = kw.get('tooltip_value')
        self.tooltip_image_size = kw.get('tooltip_image_size',
                                         gtk.ICON_SIZE_DIALOG)

    def search_by(self, objectlist):
        """Search by this column on an ObjectList

        :param objectlist: An ObjectList or ObjectTree
        """
        objectlist.set_search_equal_func(self._search_equal_func)

    def render_tooltip(self, tooltip, obj):
        """Render the tooltip for this column for an object
        """
        if self.tooltip_attr:
            val = getattr(obj, self.tooltip_attr)
        elif self.tooltip_value:
            val = self.tooltip_value
        else:
            return False
        setter = getattr(tooltip, TOOLTIP_SETTERS.get(self.tooltip_type))
        if self.tooltip_type in TOOLTIP_SIZED_TYPES:
            setter(val, self.tooltip_image_size)
        else:
            setter(val)
        return True

    def _default_sort_func(self, model, iter1, iter2, objectlist):
        attr1 = getattr(objectlist._object_at_child_sort_iter(iter1),
                        self.attr, None)
        attr2 = getattr(objectlist._object_at_child_sort_iter(iter2),
                        self.attr, None)
        if self.sort_key:
            attr1 = self.sort_key(attr1)
            attr1 = self.sort_key(attr2)
        return self.sort_func(attr1, attr2)

    def _search_equal_func(self, model, column, key, iter):
        obj = model[iter][0]
        val = getattr(obj, self.attr)
        if self.search_key is not None:
            val = self.search_key(val)
        # return False for success!
        return not (key.lower() in str(val).lower())

    def _on_viewcol_clicked(self, view_col):
        return #
        print view_col
        print view_col.get_sort_order()



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

    def remove(self, item):
        """Remove an item from the list

        :param item: The item to remove from the list.
        :raises ValueError: If the item is not present in the list.
        """
        if item not in self:
            raise ValueError('objectlist.remove(item) failed, item not in list')
        giter = self._iter_for(item)
        del self[giter]

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
        #print model, selected
        if selected is not None:
            return self._object_at_sort_iter(selected)

    def _set_selected_item(self, item):
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_SINGLE:
            raise AttributeError('selected_item not valid for select_multiple')
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
        for item in new_selection:
            selection.select_iter(self._sort_iter_for(item))

    selected_items = property(
            fget=_get_selected_items,
            fset=_set_selected_items,
            #XXX: fdel for deselect?
            doc=_get_selected_items.__doc__,
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
        self.get_selection().connect('changed', self._on_selection_changed)

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




class ObjectList(ObjectTreeViewBase):
    """An object list
    """

    __gtype_name__ = "PyGTKHelpersObjectList"

    def create_model(self):
        return gtk.ListStore(object)

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

    def extend(self, iter):
        """Add a sequence of items to the end of the list

        :param iter: The iterable of items to add.
        """
        for item in iter:
            self.append(item)


class ObjectTree(ObjectTreeViewBase):
    """An object tree
    """

    __gtype_name__ = "PyGTKHelpersObjectTree"

    gsignal('item-expanded', object)
    gsignal('item-collapsed', object)

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
        return self.emit('item-expanded', self._object_at_sort_iter(giter))

    def _on_row_collapsed(self, objecttree, giter, path):
        return self.emit('item-collapsed', self._object_at_sort_iter(giter))


class EditableCellMixin(object):

    def __init__(self, cell, objectlist):
        gtk.CellRendererText.__init__(self)
        self.cell = cell
        self.objectlist = objectlist
        self.set_property('editable', cell.editable)
        if cell.editable:
            self.connect('edited', self._on_edited)

    def _on_edited(self, cellrenderer, path, text):
        obj = self.objectlist[path]
        #XXX: full converter
        value = self.cell.type(text)
        setattr(obj, self.cell.attr, value)
        self.objectlist.emit('item-changed', obj, self.cell.attr, value)


class CellRendererText(EditableCellMixin, gtk.CellRendererText):

    def __init__(self, cell, objectlist):
        gtk.CellRendererText.__init__(self)
        EditableCellMixin.__init__(self, cell, objectlist)
        ellipsize = cell.kwargs.get('ellipsize')
        if ellipsize is not None:
            self.set_property('ellipsize', ellipsize)


class CellRendererSpin(EditableCellMixin, gtk.CellRendererSpin):

    def __init__(self, cell, objectlist):
        gtk.CellRendererSpin.__init__(self)
        EditableCellMixin.__init__(self, cell, objectlist)
        adj = cell.kwargs.get('adjustment', None)
        if adj is None:
            smin = cell.kwargs.get('min', 0)
            smax = cell.kwargs.get('max', 2 ** 20)
            step = cell.kwargs.get('step', 1)
            adj = gtk.Adjustment(0, smin, smax, step)
        self.set_property('adjustment', adj)
        digits = cell.kwargs.get('digits', None)
        if digits is None:
            if cell.type is float:
                digits = 2
            else:
                digits = 0
        self.set_property('digits', digits)


    def _on_edited(self, cellrenderer, path, text):
        obj = self.objectlist[path]
        #XXX: full converter
        value = self.cell.type(text)
        setattr(obj, self.cell.attr, value)
        self.objectlist.emit('item-changed', obj, self.cell.attr, value)


class CellRendererToggle(gtk.CellRendererToggle):

    def __init__(self, cell, objectlist):
        gtk.CellRendererToggle.__init__(self)
        self.cell = cell
        self.objectlist = objectlist
        self.set_property('radio', not cell.use_checkbox)
        self.set_property('activatable', cell.editable)
        if cell.editable:
            self.connect('toggled', self._on_toggled)

    def _on_toggled(self, cellrenderer, path):
        obj = self.objectlist._object_at_path(path)
        value = not getattr(obj, self.cell.attr)
        setattr(obj, self.cell.attr, value)
        self.objectlist.emit('item-changed', obj, self.cell.attr, value)

class CellRendererProgress(gtk.CellRendererProgress):

    def __init__(self, cell, objectlist):
        gtk.CellRendererProgress.__init__(self)
        self.cell = cell
        self.objectlist = objectlist
        text = cell.kwargs.get('progress_text')
        if text is not None:
            self.set_property('text', text)

class CellRendererCombo(gtk.CellRendererCombo):

    def __init__(self, cell, objectlist, choices):
        gtk.CellRendererCombo.__init__(self)
        self.cell = cell
        self.objectlist = objectlist
        self.props.model = gtk.ListStore(object, str)
        self.props.text_column = 1
        for choice in choices:
            if not isinstance(choice, tuple):
                choice = (choice, choice)
            self.props.model.append(choice)
        self.props.editable = True
        self.connect('changed', self._on_changed)

    def _on_changed(self, _, path, new_iter):#XXX:
        obj = self.objectlist[path]
        value = self.props.model[new_iter][0]
        setattr(obj, self.cell.attr, value)
        self.objectlist.emit('item-changed', obj, self.cell.attr, value)


TOOLTIP_TEXT = 'text'
TOOLTIP_MARKUP = 'markup'
TOOLTIP_PIXBUF = 'pixbuf'
TOOLTIP_STOCK = 'stock'
TOOLTIP_ICONNAME = 'iconname'
TOOLTIP_CUSTOM = 'custom'

TOOLTIP_SETTERS = {
    TOOLTIP_TEXT: 'set_text',
    TOOLTIP_MARKUP: 'set_markup',
    TOOLTIP_PIXBUF: 'set_icon',
    TOOLTIP_ICONNAME: 'set_icon_from_icon_name',
    TOOLTIP_STOCK: 'set_icon_from_stock',
    TOOLTIP_CUSTOM: 'set_custom',
}

TOOLTIP_TYPES = set(TOOLTIP_SETTERS)

TOOLTIP_SIZED_TYPES = set([
    TOOLTIP_STOCK, TOOLTIP_ICONNAME
])

