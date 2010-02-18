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


class SetPropertyRenderer(object):

    def __init__(self, prop, attr=None):
        self.prop = prop
        self.attr = attr

    def __call__(self, mapper, object, cell):
        # attr is None implementation uses the cell
        cell.set_property(self.prop, mapper.from_object(object, self.attr))


text_renderer = SetPropertyRenderer('text')
markup_renderer = SetPropertyRenderer('markup')
pixbuf_renderer = SetPropertyRenderer('pixbuf')
stockid_renderer = SetPropertyRenderer('stock-id')


class Cell(object):

    def __init__(self, attr, type=str, editable=False, renderers=None,
                     use_stock=False, use_markup=False, choices=None,
                     format_func=None,
                     ellipsize=None):
        self.attr = attr
        self.type = type
        self.format = "%s"
        self.editable = editable
        self.use_markup = use_markup
        self.use_stock = use_stock
        self.choices = choices
        self.ellipsize = ellipsize
        if use_stock:
            self.renderers = [stockid_renderer]
        elif type==gtk.gdk.Pixbuf:
            self.renderers = [pixbuf_renderer]
        elif use_markup:
            self.renderers = [markup_renderer]
        else:
            self.renderers = renderers or [text_renderer]
        if format_func is not None:
            self.format_data = format_func

    def __repr__(self):
        return '<Cell %s %r>'%(self.attr, self.type)

    def from_object(self, object, attr=None):
        #XXX allow a callback?
        if attr is None:
            attr = self.attr
        return getattr(object, attr)

    def format_data(self, data):
        return self.format%data

    def render(self, object, cell):
        for renderer in self.renderers:
            renderer(self, object, cell)

    def _data_func(self, column, cell, model, iter):
        obj = model.get_value(iter, 0)
        self.render(obj, cell)

    def create_renderer(self, column, objectlist):
        #XXX: extend to more types
        if self.use_stock or self.type == gtk.gdk.Pixbuf:
            cell = gtk.CellRendererPixbuf()
        elif self.choices:
            #XXX: a mapping?
            if isinstance(self.choices[0], tuple):
                model = gtk.ListStore(str, str) #XXX: hack, propper types
                text_col = 1
            else:
                model = gtk.ListStore(str) #XXX: hack, propper types
                text_col = 0


            for choice in self.choices:
                if not isinstance(choice, tuple):
                    choice = [choice]
                model.append(choice)
            cell = gtk.CellRendererCombo()
            cell.props.model = model
            cell.props.editable = True
            cell.props.text_column = text_col
            def changed(_, path, new_iter):#XXX:
                object = objectlist[path]
                #XXX: full converter
                value = cell.props.model[new_iter][0]

                setattr(object, self.attr, value)
                objectlist.emit('item-changed', object, self.attr, value)
            cell.connect('changed', changed)
        else:
            cell = gtk.CellRendererText()
            cell.props.editable = self.editable
            if self.ellipsize is not None:
                cell.props.ellipsize = self.ellipsize

        cell.set_data('pygtkhelpers::cell', self)
        if self.editable and not self.choices:
            def simple_set(cellrenderer, path, text):
                object = objectlist[path]
                #XXX: full converter
                value = self.type(text)
                setattr(object, self.attr, value)
                objectlist.emit('item-changed', object, self.attr, value)
            cell.connect('edited', simple_set)
        return cell


class Column(gtk.TreeViewColumn):
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


        if 'cells' in kwargs:
            self.cells = kwargs['cells']
        else:
            #XXX: sane arg filter
            self.cells = [Cell(attr, type, **kwargs)]

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
            #XXX: better controll over packing
            col.pack_start(view_cell)
            col.set_cell_data_func(view_cell, cell._data_func)
        return col


class ObjectList(gtk.TreeView):
    __gtype_name__ = "PyGTKHelpersObjectList"
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
        self.model = gtk.ListStore(object)
        self.set_model(self.model)

        # setup sorting
        self.sortable = kwargs.pop('sortable', True)
        sort_func = kwargs.pop('sort_func', self._default_sort_func)
        self.columns = None
        self.set_columns(columns)

        # connect internal signals
        self.connect('button-press-event', self._on_button_press_event)
        self.get_selection().connect('changed', self._on_selection_changed)

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

    def append(self, item, select=False):
        if item in self:
            raise ValueError("item %s allready in list"%item )
        modeliter = self.model.append((item,))
        self._id_to_iter[id(item)] = modeliter
        if select:
            self.selected_item = item

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

    def extend(self, iter):
        for item in iter:
            self.append(item)

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


