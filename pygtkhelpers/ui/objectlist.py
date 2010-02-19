# -*- coding: utf-8 -*-

"""
    pygtkhelpers.ui.objectlist
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    ListViews that are object orientated, and mimic Pythonic lists

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

    def __call__(self, cell, obj, renderer):
        value = getattr(obj, self.attr or cell.attr)
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
        # attribute and type
        self.attr = attr
        self.type = type

        # behaviour
        self.editable = kw.get('editable', False)
        self.choices = kw.get('choices', [])

        # display
        self.use_markup = kw.get('use_markup', False)
        self.use_stock = kw.get('use_stock', False)
        self.ellipsize = kw.get('ellipsize', None)

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

        # formatting
        self.format = kw.get('format', '%s')
        self.format_data = kw.get('format_func') or self.format_data

    @property
    def primary_mapper(self):
        return self.mappers[0]

    def format_data(self, data):
        return self.format % data

    def render(self, object, cell):
        for mapper in self.mappers:
            mapper(self, object, cell)

    def cell_data_func(self, column, cell, model, iter):
        obj = model.get_value(iter, 0)
        self.render(obj, cell)

    def create_renderer(self, column, objectlist):
        #XXX: extend to more types
        if self.use_stock or self.type == gtk.gdk.Pixbuf:
            cell = gtk.CellRendererPixbuf()
        elif self.choices:
            #XXX: a mapping?
            cell = CellRendererCombo(self, objectlist, self.choices)
        else:
            cell = CellRendererText(self, objectlist)
        cell.set_data('pygtkhelpers::cell', self)
        return cell

    def _calculate_primary_prop(self):
        if self.use_stock:
            primary_prop = 'stock-id'
        elif self.type==gtk.gdk.Pixbuf:
            primary_prop = 'pixbuf'
        elif self.use_markup:
            primary_prop = 'markup'
        else:
            primary_prop = 'text'
        return primary_prop

    def __repr__(self):
        return '<Cell %s %r>'%(self.attr, self.type)



class Column(object):
    #XXX: handle cells propperly

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

        if 'cells' in kwargs:
            self.cells = kwargs['cells']
        else:
            #XXX: sane arg filter
            self.cells = [Cell(attr, type, **kwargs)]

        # tooltips are per column, not per cell
        self._init_tooltips(**kwargs)

    def create_treecolumn(self, objectlist):
        col = gtk.TreeViewColumn(self.title)
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
        return col


    def _init_tooltips(self, **kw):
        self.tooltip_attr = kw.get('tooltip_attr')
        self.tooltip_type = kw.get('tooltip_type', TOOLTIP_TEXT)
        if self.tooltip_type not in TOOLTIP_TYPES:
            raise ValueError('Tooltip types must be in %r.' % TOOLTIP_TYPES)
        self.tooltip_value = kw.get('tooltip_value')
        self.tooltip_image_size = kw.get('tooltip_image_size',
                                         gtk.ICON_SIZE_DIALOG)


    def render_tooltip(self, tooltip, obj):
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




class ObjectTreeViewBase(gtk.TreeView):

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
        self.set_model(self.model)

        # setup sorting
        self.sortable = kwargs.pop('sortable', True)
        sort_func = kwargs.pop('sort_func', self._default_sort_func)
        self.columns = None
        self.set_columns(columns)

        # misc initial setup
        self.set_property('has-tooltip', kwargs.pop('show_tooltips', True))

        self._connect_internal()

    def create_model(self):
        raise NotImplementedError

    def set_columns(self, columns):
        assert not self.columns
        self.columns = tuple(columns)
        for idx, col in enumerate(columns):
            view_col = col.create_treecolumn(self)
            view_col.set_reorderable(True)
            view_col.set_sort_indicator(False)
            # Hack to make soring work right.  Does not sort.
            view_col.set_sort_order(gtk.SORT_DESCENDING)

            if self.sortable and col.sorted:
                self.model.set_sort_func(idx, self._default_sort_func,
                                         (col, col.attr))
                view_col.set_sort_column_id(idx)
                view_col.connect('clicked', self.set_sort_by, idx)

            view_col.set_data('pygtkhelpers::objectlist', self)
            self.append_column(view_col)

            # needs to be done after adding the column
            if col.expander:
                self.set_expander_column(view_col)

        self._id_to_iter = {}

        def on_row_activated(self, path, column, *k):
            self.emit('item-activated', self.model[path][0])
        self.connect('row-activated', on_row_activated)

    def set_sort_by(self, column, idx):
        current = column.get_sort_order
        asc, desc = gtk.SORT_ASCENDING, gtk.SORT_DESCENDING
        order = desc if column.get_sort_order() == asc else asc

        title = column.get_title()
        for col in self.get_columns():
            if title == col.get_title():
                order = desc if column.get_sort_order() == asc else asc
                col.set_sort_indicator(True)
                col.set_sort_order(order)
            else:
                col.set_sort_indicator(False)
                col.set_sort_order(gtk.SORT_DESCENDING)

    def _default_sort_func(self, model, iter1, iter2, data=None):
        idx, order = self.model.get_sort_column_id()
        get_value = self.model.get_value
        return cmp(get_value(iter1, 0), get_value(iter2, 0))

    def __len__(self):
        return len(self.model)

    def __contains__(self, item):
        """identity based check of membership"""
        return id(item) in self._id_to_iter

    def __iter__(self):
        for row in self.model:
            yield row[0]

    def __getitem__(self, index):
        # index can be an integer or an iter
        return self._object_at_iter(index)

    def __delitem__(self, iter): #XXX
        obj = self._object_at_iter(iter)
        del self._id_to_iter[id(obj)]
        self.model.remove(iter)


    @property
    def selected_item(self):
        """The currently selected item"""
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_SINGLE:
            raise AttributeError('selected_item not valid for select_multiple')
        model, selected = selection.get_selected()
        if selected is not None:
            return self._object_at_iter(selected)

    @selected_item.setter
    def selected_item(self, item):
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_SINGLE:
            raise AttributeError('selected_item not valid for select_multiple')
        giter = self._iter_for(item)
        selection.select_iter(giter)
        self.set_cursor(self.model[giter].path)

    @property
    def selected_items(self):
        """List of currently selected items"""
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_MULTIPLE:
            raise AttributeError('selected_items only valid for select_multiple')
        model, selected_paths = selection.get_selected_rows()
        result = []
        for path in selected_paths:
            result.append(model[path][0])
        return result

    @selected_items.setter
    def selected_items(self, new_selection):
        selection = self.get_selection()
        if selection.get_mode() != gtk.SELECTION_MULTIPLE:
            raise AttributeError('selected_items only valid for select_multiple')

        for item in new_selection:
            selection.select_iter(self._iter_for(item))

    def clear(self):
        self.model.clear()
        self._id_to_iter.clear()

    def update(self, item):
        self.model.set(self._iter_for(item), 0, item)

    def _iter_for(self, obj):
        return self._id_to_iter[id(obj)]

    def _path_for(self, obj):
        return self.model.get_string_from_iter(self._iter_for(obj))

    def _object_at_iter(self, iter):
        return self.model[iter][0]

    def _object_at_path(self, path):
        return self._object_at_iter(self.model.get_iter(path))

    def _connect_internal(self):
        # connect internal signals
        self.connect('button-press-event', self._on_button_press_event)
        self.connect('query-tooltip', self._on_query_tooltip)
        self.get_selection().connect('changed', self._on_selection_changed)

    def _emit_for_path(self, path, event):
        item = self._object_at_path(path)
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
            path, column, rx, ry = self.get_path_at_pos(tx, ty)
            obj = self._object_at_path(path)
            pcol = column.get_data('pygtkhelpers::column')
            return pcol.render_tooltip(tooltip, obj)



class ObjectList(ObjectTreeViewBase):

    __gtype_name__ = "PyGTKHelpersObjectList"

    def create_model(self):
        return gtk.ListStore(object)

    def append(self, item, select=False):
        if item in self:
            raise ValueError("item %s allready in list"%item )
        modeliter = self.model.append((item,))
        self._id_to_iter[id(item)] = modeliter
        if select:
            self.selected_item = item

    def extend(self, iter):
        for item in iter:
            self.append(item)


class ObjectTree(ObjectTreeViewBase):

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
        for item in iter:
            self.append(item, parent)

    def expand_item(self, item, open_all=True):
        self.expand_row(self._path_for(item), open_all)

    def collapse_item(self, item):
        self.collapse_row(self._path_for(item))

    def item_expanded(self, item):
        return self.row_expanded(self._path_for(item))

    def _on_row_expanded(self, objecttree, giter, path):
        self.emit('item-expanded', self._object_at_iter(giter))

    def _on_row_collapsed(self, objecttree, giter, path):
        self.emit('item-collapsed', self._object_at_iter(giter))


class EditableCellRendererMixin(object):

    copy_properties = []

    def __init__(self, cell, objectlist):
        self.cell = cell
        self.objectlist = objectlist
        self.props.editable = cell.editable
        for prop in self.copy_properties:
            value = getattr(cell, prop)
            if value is not None:
                self.set_property(prop, getattr(cell, prop))
        if cell.editable:
            self.connect('edited', self._on_edited)

    def _on_edited(self, cellrenderer, path, text):
        obj = self.objectlist[path]
        #XXX: full converter
        value = self.cell.type(text)
        setattr(obj, self.cell.attr, value)
        self.objectlist.emit('item-changed', obj, self.cell.attr, value)


class CellRendererText(EditableCellRendererMixin, gtk.CellRendererText):

    copy_properties = ['ellipsize']

    def __init__(self, cell, objectlist):
        gtk.CellRendererText.__init__(self)
        EditableCellRendererMixin.__init__(self, cell, objectlist)



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
