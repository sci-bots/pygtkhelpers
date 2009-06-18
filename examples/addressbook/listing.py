import gtk
from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.objectlist import ObjectList, Column
from pygtkhelpers.utils import run_in_window, gsignal

from person import Person, from_json, to_json




class PersonList(SlaveView):
    gsignal('item-activated', object)

    columns = [
        Column('name', str),
        Column('surname', str),
        Column('email', str),
    ]

    def __init__(self):
        SlaveView.__init__(self)
        self.current_file = None

    def create_ui(self):
        self.objects = ObjectList(self.columns)
        self.widget.add(self.objects)

        self.buttons = gtk.Toolbar()
        self.widget.pack_end(self.buttons, 0, 0, 0)
        def button(stock):
            button = gtk.ToolButton(stock)
            self.buttons.add(button)
            return button

        self.add = button(gtk.STOCK_ADD)
        self.remove = button(gtk.STOCK_REMOVE)

        self.new = button(stock=gtk.STOCK_NEW)
        self.open = button(stock=gtk.STOCK_OPEN)

        self.save = button(stock=gtk.STOCK_SAVE)
        self.save_as = button(stock=gtk.STOCK_SAVE_AS)

    def on_objects__item_activated(self, listing, item):
        self.emit('item-activated', item)

    def on_add__clicked(self, *k):
        #XXX. better values or editing
        self.objects.append(Person('None', 'None', 'None'))



    def _select_file(self):
        finder = gtk.FileChooserDialog(
            buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            )
        response = finder.run()
        if gtk.RESPONSE_OK == response:
            self.current_file = finder.get_filename()
        finder.destroy()

    def on_save_as__clicked(self, widget):
        self._select_file()
        self.on_save__clicked(widget)

    def on_save__clicked(self, _):
        assert self.current_file #XXX: error message?
        to_json(self.objects, self.current_file)

    def on_new__clicked(self, _):
        self.objects.clear()
        self.current_file = None

    def on_open__clicked(self, _):
        self.objects.clear()
        self._select_file()
        self.objects.extend(from_json(self.current_file))

    def on_remove__clicked(self, _):
        #XXX: simplify later
        selection = self.objects.get_selection()
        # assume no select_multiple
        model, iter = selection.get_selected()
        del self.objects[iter]


if __name__ == '__main__':
    listing = PersonList()
    run_in_window(listing)
