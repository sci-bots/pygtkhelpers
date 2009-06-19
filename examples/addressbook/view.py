import gtk
from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.utils import run_in_window

from listing import PersonList
from form import PersonForm

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

    def on_detail__model_updated(self, detail):
        self.listing.objects.update(detail.model)

if __name__ == '__main__':
    editor = PersonEditor()
    run_in_window(editor)

