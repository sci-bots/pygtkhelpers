import gtk
from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.objectlist import ObjectList, Column
from pygtkhelpers.utils import run_in_window, gsignal

from person import Person, from_json, to_json




class PersonList(SlaveView):
    gsignal('item-activated', object)

    def __init__(self):
        SlaveView.__init__(self)
        self.current_file = None

    def create_ui(self):
        columns = [
            Column('name', str),
            Column('surname', str),
            Column('email', str),
        ]
        self.objects = ObjectList(columns)
        self.widget.add(self.objects)

    def on_objects__item_activated(self, listing, item):
        self.emit('item-activated', item)

    def append_item(self, item):
        self.objects.append(item)


if __name__ == '__main__':
    listing = PersonList()
    listing.append_item(Person('Ali', 'Afshar', 'aafshar@gmail.com'))
    listing.append_item(Person('Hilda', 'Afshar', 'hafshar@gmail.com'))
    run_in_window(listing)
