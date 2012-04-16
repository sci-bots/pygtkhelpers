# -*- coding: utf-8 -*-

"""
    pygtkhelpers.ui.objectlist.column
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk, gobject


class PropertyMapper(object):

    def __init__(self, prop, attr=None, format_func=None):
        self.prop = prop
        self.attr = attr
        # Check to see if this is the primary attribute, and also there is
        # format string, we do this once, so we don't check on every update.
        self.format_func = format_func

    def __call__(self, cell, obj, renderer):
        attr = self.attr or cell.attr
        value = obj if attr is None else getattr(obj, attr)
        if self.format_func:
            value = self.format_func(value)
        renderer.set_property(self.prop, value)


class CellMapper(object):

    def __init__(self, map_spec):
        self.mappers = []
        for prop, attr in map_spec.items():
            # the user may either specify a function to compute the attribute or a fixed attribute.
            if callable(attr):
                self.mappers.append(PropertyMapper(prop, format_func=attr))
            else:
                self.mappers.append(PropertyMapper(prop, attr))

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
        self.mappers = kw.get('mappers', [])
        self.mapped = kw.get('mapped', {})
        
        #XXX: cellmapper needs to die
        if self.mapped:
            self.mappers.append(CellMapper(self.mapped))
        if self.attr:
            default_prop = self._calculate_default_prop()
            self.mappers.append(PropertyMapper(default_prop, attr=self.attr, format_func=self.format_data))

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

    def _calculate_default_prop(self):
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
    :param resizable: Whether the user can resize the column
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

        self.title = title or attr.capitalize()
        self.attr = attr
        self.sorted = kwargs.pop('sorted', True)
        self.expand = kwargs.pop('expand', None)
        self.visible = kwargs.pop('visible', True)
        self.width = kwargs.pop('width', None)
        self.expander = kwargs.pop('expander', None)
        self.resizable = kwargs.pop('resizable', None)
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
        if self.resizable is not None:
            col.props.resizable = self.resizable
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
        assert model is objectlist.model_filter  # the filtermodel gets sorted
        attr1 = getattr(model[iter1][0], self.attr, None)
        attr2 = getattr(model[iter2][0], self.attr, None)
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



class EditableCellMixin(object):

    def __init__(self, cell, objectlist):
        gtk.CellRendererText.__init__(self)
        self.cell = cell
        self.objectlist = objectlist
        self.set_property('editable', cell.editable)
        if cell.editable:
            self.connect('edited', self._on_edited)

    def _on_edited(self, cellrenderer, path, text):
        obj = self.objectlist._object_at_sort_path(path)
        #XXX: full converter
        #XXX: breaks if attr is None
        value = self.cell.type(text)
        original_value = getattr(obj, self.cell.attr)
        if value != original_value:
            # Only trigger update if value has actually changed
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
        obj = self.objectlist._object_at_sort_path(path)
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
        original_value = getattr(obj, self.cell.attr)
        if value != original_value:
            # Only trigger update if value has actually changed
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

