import gtk

class Column(object):
    def __init__(self, attr, type):
        self.attr = attr
        self.type = type


    #XXX: might be missplaced
    def _data_func(self, column, cell, model, iter):
        obj = model.get_value(iter, 0)
        #XXX: types
        cell.set_property('text', getattr(obj, self.attr))

    #XXX: might be missplaced
    @property
    def viewcolumn(self):
        title = self.attr.capitalize()
        col = gtk.TreeViewColumn(title)
        #XXX: extend to more types
        cell = gtk.CellRendererText()
        col.pack_start(cell)
        col.set_cell_data_func(cell, self._data_func)
        return col

class ObjectList(gtk.TreeView):

    def __init__(self, columns=(), filtering=False, sorting=False):
        gtk.TreeView.__init__(self)

        self.treeview = gtk.TreeView()
        #XXX: make replacable
        self.model = gtk.ListStore(object)
        self.set_model(self.model)

        self.columns = tuple(columns)
        for col in columns:
            self.append_column(col.viewcolumn)
    
    def __len__(self):
        return len(self.model)

    def __getitem__(self, index):
        return self.model[index][0]

    def append(self, item):
        self.model.append((item,))

