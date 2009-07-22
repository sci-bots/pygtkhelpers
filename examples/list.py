import gtk
from pygtkhelpers.ui.objectlist import Column, ObjectList


class User(object):
    def __init__(self, name, age):
        self.name = name
        self.age = age

listing = ObjectList([
    Column('name', str, editable=True),
    Column('age', int, editable=True),
    ])

listing.append(
    User("test", 12)
    )
listing.extend([
    User('hans', 34),
    User('Zok', 60),
    ])

window = gtk.Window()
window.add(listing)

window.connect("destroy", gtk.main_quit)
window.show_all()
gtk.main()
