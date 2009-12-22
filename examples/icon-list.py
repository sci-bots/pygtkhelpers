import gtk
from pygtkhelpers.ui.objectlist import ObjectList, Cell, Column





class IconInfo(object):
    def __init__(self, stock_name, name):
        self.stock_name = stock_name
        self._name = name

    @property
    def name(self):
        return '<b>%s</b>'%self._name

icons = ObjectList([
    Column(title='Stock Data', cells=[
        Cell('stock_name', gtk.Pixmap, use_stock=True),
        Cell('stock_name', str),
        ], sorted=False),
    Column('name', str, 'Name', use_markup=True),
], sortable=True)

for id in gtk.stock_list_ids():
    lookup = gtk.stock_lookup(id)
    if lookup is None:
        continue
    stock_name, name = gtk.stock_lookup(id)[:2]
    name = name.replace('_', '')
    icons.append(IconInfo(stock_name, name))

scroll = gtk.ScrolledWindow()
scroll.add(icons)

win = gtk.Window()
win.add(scroll)
win.set_size_request(600, 400)

win.show_all()
win.connect('destroy', gtk.main_quit)
gtk.main()
