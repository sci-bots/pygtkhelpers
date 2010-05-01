import gtk
from pygtkhelpers.ui.objectlist import Column, ObjectList





class User(object):
    def __init__(self, name, age, sex):
        self.name = name
        self.age = age
        assert sex in ('m','f')
        self.sex = sex

    def __str__(self):
        return '<User: name=%r age=%r sex=%r>' % (self.name, self.age,
                                                  self.sex)



listing = ObjectList([
    Column('name', str, editable=False),
    Column('age', int, editable=True),
    Column('sex', str, choices=[
        ('m', 'Male'),
        ('f', 'Female'),
        ]),
    ])

def _on_left_clicked(ol, item, event):
    print 'Left clicked', item

def _on_right_clicked(ol, item, event):
    print 'Right clicked', item

def _on_middle_clicked(ol, item, event):
    print 'Middle clicked', item

def _on_double_clicked(ol, item, event):
    print 'Double clicked', item

def _on_item_activated(ol, item):
    print 'Item activated', item

listing.connect('item-left-clicked', _on_left_clicked)
listing.connect('item-right-clicked', _on_right_clicked)
listing.connect('item-middle-clicked', _on_middle_clicked)
listing.connect('item-double-clicked', _on_double_clicked)
listing.connect('item-activated', _on_item_activated)

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
