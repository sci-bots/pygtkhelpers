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

class ObjectList(gtk.ScrolledWindow):

    def __init__(self, columns=(), filtering=False, sorting=False):
        gtk.ScrolledWindow.__init__(self)
        
        self.treeview = gtk.TreeView()
        #XXX: make replacable
        self.store = gtk.ListStore(object)
        self.treeview.set_model(self.store)
        #XXX: allow user defined
        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER) 
        self.add(self.treeview)
        self.columns = tuple(columns)
        for col in columns:
            self.treeview.append_column(col.viewcolumn)

    def append(self, item):
        self.store.append((item,))

