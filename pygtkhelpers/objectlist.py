import gtk
from pygtkhelpers.utils import gsignal


def set_text_renderer(mapper, object, cell):
    cell.set_property('text', mapper.from_object(object))

def set_stock_renderer(mapper, object, cell):
    cell.set_property('stock-id', mapper.from_object(object))

class Cell(object):
    def __init__(self, attr, type=str, editable=False, renderers=None, use_stock=False):
        self.attr = attr
        self.type = type
        self.format = "%s"
        self.editable = editable
        self.use_stock = use_stock
        if use_stock:
            self.renderers = [set_stock_renderer]
        else:
            self.renderers = renderers or [set_text_renderer]

    def __repr__(self):
        return '<Cell %s %r>'%(self.attr, self.type)

    def from_object(self, object):
        #XXX allow a callback?
        return getattr(object, self.attr)

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
        if self.use_stock:
            cell = gtk.CellRendererPixbuf()
        else:
            cell = gtk.CellRendererText()
            cell.props.editable = self.editable
        cell.set_data('pygtkhelpers::cell', self)
        if self.editable:
            def simple_set(cellrenderer, path, text):
                object = objectlist[path]
                #XXX: full converter
                value = self.type(text)
                setattr(object, self.attr, value)
                objectlist.emit('item-changed', object, self.attr, value)
            cell.connect('edited', simple_set)
        return cell

class Column(object):
    #XXX: handle cells propperly
    def __init__(self, attr=None, type=str, title=None, **kw):

        #XXX: better error messages
        assert title or attr, "Columns need a title or an attribute to infer it"
        assert attr or 'cells' in kw, 'Columns need a attribute or a set of cells'

        self.title = title or attr.capitalize()

        if 'cells' in kw:
            self.cells = kw['cells']
        else:
            #XXX: sane arg filter
            self.cells = [Cell(attr, type, **kw)] 


    def create_treecolumn(self, objectlist):
        col = gtk.TreeViewColumn(self.title)
        col.set_data('pygtkhelpers::column', self)
        for cell in self.cells:
            view_cell = cell.create_renderer(self, objectlist)
            view_cell.set_data('pygtkhelpers::column', self)
            #XXX: better controll over packing
            col.pack_start(view_cell)
            col.set_cell_data_func(view_cell, cell._data_func)
        return col

class ObjectList(gtk.TreeView):

    gsignal('item-activated', object)
    gsignal('item-changed', object, str, object)

    def __init__(self, columns=(), filtering=False, sorting=False):
        gtk.TreeView.__init__(self)

        self.treeview = gtk.TreeView()
        #XXX: make replacable
        self.model = gtk.ListStore(object)
        self.set_model(self.model)

        self.columns = tuple(columns)
        for col in columns:
            view_col = col.create_treecolumn(self)
            view_col.set_data('pygtkhelpers::objectlist', self)
            self.append_column(view_col)

        self._id_to_iter = {}

        def on_row_activated(self, path, column, *k):
            self.emit('item-activated', self.model[path][0])
        self.connect('row-activated', on_row_activated)

    def __len__(self):
        return len(self.model)

    def __contains__(self, item):
        """identity based check of membership"""
        return id(item) in self._id_to_iter

    def __iter__(self):
        for row in self.model:
            yield row[0]

    def __getitem__(self, index):
        return self.model[index][0]

    def __delitem__(self, iter): #XXX
        obj = self.model[iter][0]
        del self._id_to_iter[id(obj)]
        self.model.remove(iter)

    def append(self, item):
        if item in self:
            raise ValueError("item %s allready in list"%item )
        modeliter = self.model.append((item,))
        self._id_to_iter[id(item)] = modeliter

    def extend(self, iter):
        for item in iter:
            self.append(item)

    def clear(self):
        self.model.clear()
        self._id_to_iter.clear()

    def update(self, item):
        iter = self._id_to_iter[id(item)]
        self.model.set(iter, 0, item)


    def _path_for(self, object):
        oid = id(object)
        if oid in self._id_to_iter:
            return self.model.get_string_from_iter(self._id_to_iter[oid])

