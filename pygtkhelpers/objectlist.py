import gtk
from pygtkhelpers.utils import gsignal



class Cell(object):
    def __init__(self, attr, type=str):
        self.attr = attr
        self.type = type
        self.format = "%s"


    def from_object(self, object):
        #XXX allow a callback?
        return getattr(object, self.attr)

    def format_data(self, data):
        return self.format%data

    def _data_func(self, column, cell, model, iter):
        obj = model.get_value(iter, 0)
        data = self.from_object(obj)
        #XXX: types
        cell.set_property('text', self.format_data(data))

    def make_viewcell(self):
        #XXX: extend to more types
        return gtk.CellRendererText()

class Column(object):
    #XXX: handle cells propperly
    def __init__(self, attr=None, type=str, title=None, **kw):

        #XXX: better error messages
        assert title or attr, "Columns need a title or an attribute to infer it"
        assert attr or 'cells' in kw, 'Columns need a attribute or a set of cells'

        self.title = title or attr.capitalize()

        self.cells = [ Cell(attr, type)]


    def make_viewcolumn(self):
        col = gtk.TreeViewColumn(self.title)
        for cell in self.cells:
            view_cell = cell.make_viewcell()
            #XXX: better controll over packing
            col.pack_start(view_cell)
            col.set_cell_data_func(view_cell, cell._data_func)
        return col

class ObjectList(gtk.TreeView):

    gsignal('item-activated', object)

    def __init__(self, columns=(), filtering=False, sorting=False):
        gtk.TreeView.__init__(self)

        self.treeview = gtk.TreeView()
        #XXX: make replacable
        self.model = gtk.ListStore(object)
        self.set_model(self.model)

        self.columns = tuple(columns)
        for col in columns:
            self.append_column(col.make_viewcolumn())

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

