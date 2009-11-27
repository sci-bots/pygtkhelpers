import gtk
from pygtkhelpers.ui.objectlist import Column, ObjectList





class User(object):
    def __init__(self, name, age, sex):
        self.name = name
        self.age = age
        assert sex in ('m','f')
        self.sex = sex



listing = ObjectList([
    Column('name', str, editable=True),
    Column('age', int, editable=True),
    Column('sex', str, choices=[
        ('m', 'Male'),
        ('f', 'Female'),
        ]),
    ])

listing.append(
    User("test", 12, 'm')
    )
listing.extend([
    User('hans', 34, 'm'),
    User('Zok', 60, 'm'),
    ])

window = gtk.Window()
window.add(listing)

window.connect("destroy", gtk.main_quit)
window.show_all()
gtk.main()
