import gtk
from pygtkhelpers.ui.objectlist import Column, ObjectTree





class User(object):
    def __init__(self, name, age, sex, hair='brown', clever=False):
        self.name = name
        self.age = age
        assert sex in ('m','f')
        self.sex = sex
        self.hair = hair
        self.clever = clever

    def __str__(self):
        return '<User: name=%r age=%r sex=%r hair=%r clever=%r>' % (
                                                  self.name, self.age,
                                                  self.sex, self.hair,
                                                  self.clever)



listing = ObjectTree([
    Column('name', str, editable=True, searchable=True),
    Column('age', int, editable=True),
    Column('sex', str, expander=True, choices=[
        ('m', 'Male'),
        ('f', 'Female'),
        ]),
    Column('hair', str, choices=['brown', 'blonde'],
                tooltip_attr='name'),
    Column('clever', bool, use_checkbox=True, editable=True),
    Column('age', int, use_spin=True, editable=True),
    Column('age', int, use_progress=True),
    Column('age', int, use_progress=True, progress_text='static_text'),
    Column('age', int, use_progress=True, mapped={'text': 'name'}),
    ])

def _on_left_clicked(ol, item, event):
    print 'Left clicked', item

def _on_right_clicked(ol, item, event):
    print 'Right clicked', item
    ol.sort_by('age')
    print ol.model_sort.get_sort_column_id()

def _on_middle_clicked(ol, item, event):
    ol.search_by('age')
    print 'Middle clicked', item

def _on_double_clicked(ol, item, event):
    print 'Double clicked', item
    ol.move_item_down(item)

def _on_expanded(ol, item, msg):
    print msg, item
    return True

listing.connect('item-left-clicked', _on_left_clicked)
listing.connect('item-right-clicked', _on_right_clicked)
listing.connect('item-middle-clicked', _on_middle_clicked)
listing.connect('item-double-clicked', _on_double_clicked)
listing.connect('item-expanded', _on_expanded, 'Expanded')
listing.connect('item-collapsed', _on_expanded, 'Collapsed')

u1 = User("test", 12, 'm', clever=True)
u2 = User('hans', 34, 'm', clever=True)
u3 = User('Zok', 60, 'm')
u4 = User('Mic', 63, 'f')

listing.append(u1)
listing.append(u2)
listing.append(u3, u1)
listing.append(u4, u1)

window = gtk.Window()
window.add(listing)

window.connect("destroy", gtk.main_quit)
window.show_all()
gtk.main()
