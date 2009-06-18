

import gtk

from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.utils import run_in_window

from person import Person, date


class PersonView(SlaveView):

    builder_path = 'address_form.ui'



if __name__=='__main__':
    person = Person('hans', 'man', date(1986, 03, 03))
    view = PersonView()
    view.set_model(person)
    run_in_window(view)
