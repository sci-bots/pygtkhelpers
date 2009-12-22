import gtk
from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.utils import run_in_window

from listing import PersonList
from form import PersonForm
from person import Person

class PersonEditor(SlaveView):

    def create_ui(self):
        self.pane = gtk.HPaned()
        self.widget.add(self.pane)
        self.listing = PersonList()
        self.detail = PersonForm()
        self.pane.pack1(self.listing.widget)
        self.pane.pack2(self.detail.widget)

    def on_listing__item_activated(self, listing, item):
        self.detail.model = item

    def on_listing__item_changed(self, listing, item, attr, value):
        if item is self.detail.model:
            # cause an ui update
            self.detail.model = item

    def on_detail__model_updated(self, detail, attribute, value):
        self.listing.objects.update(detail.model)

    def append_item(self, item):
        self.listing.append_item(item)

if __name__ == '__main__':
    editor = PersonEditor()
    editor.append_item(Person('Ali', 'Afshar', 'aafshar@gmail.com'))
    editor.append_item(Person('Hilda', 'Afshar', 'hafshar@gmail.com'))
    run_in_window(editor)
