import gtk
from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.utils import run_in_window
from person import Person, date


class PersonView(SlaveView):

    def __init__(self, model):
        SlaveView.__init__(self)
        self.model = model



if __name__=='__main__':
    person = Person('hans', 'man', date(1986, 03, 03))
    view = PersonView(person)
    run_in_window(view)
